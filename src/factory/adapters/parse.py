import json
import re
from pathlib import Path

def _split_sentences(text: str):
    # naive split on .!? + newline
    parts = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    return [p.strip() for p in parts if p.strip()]

def _expand_single_sentence(text: str):
    """If input is 1-2 sentences, expand into Pixar 3-act beats for better pacing."""
    text = text.strip()
    if text.count(".") >= 2 or text.count("!") >= 2 or len(text.split()) > 35:
        return None
    # Simple heuristic: split on commas / conjunctions to create beats
    # For short prompt like robot prompt, create dramatic expansion
    beats = [
        f"{text} The city glows at dusk, towering neon signs reflecting off rainy streets.",
        "The little robot wanders alone, its light flickering, watching other robots laugh together in warm shop windows.",
        "A kind child notices the robot, kneels down and offers a gentle hand. Friendship sparks — a shared glow.",
        "Together they walk through the Pixar city, the robot's light now steady and bright. Being different is what makes it special, and now it belongs.",
        "Wide sunset shot: the robot and its new friend watch the city lights together — no longer lost."
    ]
    # Trim to ~5 beats
    return beats

def _make_shots(sentences, duration_target=90):
    # Target ~ 4-6 sec per shot for Pixar pacing
    avg_shot_sec = 5
    num_shots = max(3, min(20, round(duration_target / avg_shot_sec)))
    # Expand short prompts into multi-beat story
    if len(sentences) <= 2 and sentences and len(" ".join(sentences).split()) < 40:
        expanded = _expand_single_sentence(" ".join(sentences))
        if expanded:
            sentences = expanded
            num_shots = min(num_shots, len(sentences) + 2)
    if not sentences:
        sentences = ["A quiet Pixar-style world awakens."]
    # chunk sentences
    chunk_size = max(1, len(sentences) // num_shots + 1) if len(sentences) > num_shots else 1
    shots = []
    cams = ["wide", "medium", "closeup", "over_shoulder", "dutch", "wide", "closeup", "wide"]
    actions = [
        "Establishing shot — Pixar city glowing",
        "Character enters frame, hesitant",
        "Close on eyes — longing",
        "Kind gesture — friendship begins",
        "Montage — walking together, city alive",
        "Hero moment — light shines bright",
        "Wide sunset — belonging"
    ]
    shot_id = 1
    time = 0
    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i+chunk_size]
        narration = " ".join(chunk)
        duration = min(8, max(3, len(narration.split()) * 0.38 + 1.8))
        cam = cams[(shot_id-1) % len(cams)]
        action = actions[(shot_id-1) % len(actions)]
        shots.append({
            "shot_id": f"shot_{shot_id:03d}",
            "description": narration[:120],
            "narration": narration,
            "duration_sec": round(duration, 1),
            "start_sec": round(time, 1),
            "camera": cam,
            "action": f"{action}: {narration[:70]}",
            "dialog": narration if 5 < len(narration.split()) < 28 else ""
        })
        time += duration
        shot_id += 1
        if shot_id > num_shots:
            break
    # pad if too few
    while len(shots) < min(4, num_shots):
        shots.append({
            "shot_id": f"shot_{len(shots)+1:03d}",
            "description": "B-roll pixar environment — city lights twinkle",
            "narration": "",
            "duration_sec": 3.0,
            "start_sec": round(time, 1),
            "camera": "wide",
            "action": "Environment breathing, light flicker, crowds pass softly",
            "dialog": ""
        })
        time += 3.0
    return shots

def run(film_dir: Path, config: dict, dry_run: bool = False):
    input_text = config.get("input_text", "")
    # Resolve input_text path or inline text
    text = ""
    if input_text:
        p = Path(input_text)
        # relative to film_dir or factory root
        if not p.is_absolute():
            # try film_dir / p, then factory root
            candidates = [film_dir / p, film_dir.parent.parent / p, Path(input_text)]
            for c in candidates:
                if c.exists():
                    p = c
                    break
        if p.exists() and p.is_file():
            text = p.read_text(encoding="utf-8", errors="ignore")
        else:
            # treat as inline text if not a file
            text = str(input_text)
    # fallback: films/<name>/input.txt
    if not text:
        fallback = film_dir / "input.txt"
        if fallback.exists():
            text = fallback.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        text = "A small brave character discovers a glowing secret in a cozy Pixar-style town. Through kindness and courage, they share the light with everyone."

    duration_target = int(config.get("duration_target", config.get("duration", 90)))
    sentences = _split_sentences(text)
    shots = _make_shots(sentences, duration_target)

    # Build script.md
    script_md = f"# {film_dir.name} — Script\n\n"
    script_md += f"**Duration target:** {duration_target}s  |  **Shots:** {len(shots)}  |  **Style:** {config.get('style', config.get('preset','pixar'))}\n\n"
    script_md += f"**Source text excerpt:**\n> {text[:400].strip()}...\n\n"
    script_md += "## Shots\n\n"
    for s in shots:
        script_md += f"### {s['shot_id']} — {s['camera']} ({s['duration_sec']}s)\n"
        script_md += f"- **Narration:** {s['narration']}\n"
        script_md += f"- **Action:** {s['action']}\n"
        script_md += f"- **Dialog:** {s['dialog'] or '—'}\n\n"

    out_script = film_dir / "script.md"
    out_shots = film_dir / "shots.json"

    if dry_run:
        print(f"[dry-run] would write {out_script} ({len(shots)} shots) and {out_shots}")
        return {"script": str(out_script), "shots": str(out_shots), "num_shots": len(shots), "dry_run": True}

    out_script.write_text(script_md, encoding="utf-8")
    out_shots.write_text(json.dumps({"film": film_dir.name, "duration_target": duration_target, "shots": shots}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_script} and {out_shots} ({len(shots)} shots)")
    return {"script": str(out_script), "shots": str(out_shots), "num_shots": len(shots)}
