import shutil
import subprocess
import json
from pathlib import Path

def _find_ffmpeg():
    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")

def run(film_dir: Path, config: dict, dry_run: bool = False, aspects=None):
    film_dir = Path(film_dir)
    ffmpeg = _find_ffmpeg()
    frames_dir = film_dir / "render" / "frames"
    output_dir = film_dir / "final"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve aspects
    if aspects:
        if isinstance(aspects, str):
            aspects = [a.strip() for a in aspects.split(",")]
    else:
        aspects = config.get("aspects", ["16:9"])
        if isinstance(aspects, dict):
            aspects = list(aspects.keys())

    # Find image sequence
    frames = sorted(frames_dir.glob("*.png"))
    # Also check for _RENDER_INFO placeholder
    has_frames = len(frames) > 0

    fps = config.get("render", {}).get("fps", 24)
    if isinstance(fps, dict):
        fps = 24

    if dry_run:
        print(f"[dry-run] ffmpeg={ffmpeg}, frames_found={len(frames)}, aspects={aspects}, fps={fps}")
        print(f"Would encode: {frames_dir}/frame_%04d.png -> {output_dir}/<aspect>.mp4")
        for asp in aspects:
            out = output_dir / f"{asp.replace(':','x')}.mp4"
            print(f"  - {asp}: {out}")
            if asp in ["9:16", "1:1"]:
                print(f"    -> ffmpeg -i 16x9.mp4 -vf crop=... (no re-render)")
        return {"ffmpeg": ffmpeg, "aspects": aspects, "dry_run": True}

    if not ffmpeg:
        print("ffmpeg not found — cannot export. Install ffmpeg.")
        return {"error": "ffmpeg not found"}

    if not has_frames:
        print(f"No frames in {frames_dir} — skip encoding, creating placeholder info")
        (output_dir / "_EXPORT_INFO.txt").write_text(f"No frames to encode. Run render first. Aspects: {aspects}\n", encoding="utf-8")
        return {"placeholder": True}

    # Step 1: encode master 16:9 from frames
    master = output_dir / "16x9.mp4"
    # Try common pattern
    # frames are named frame_####.png or output_####.png — we unify via glob pattern
    # We'll use input pattern detection
    # Find example frame name
    example = frames[0].name
    # Replace digits with %04d
    import re
    pattern = re.sub(r"\d+(?=\.png$)", "%04d", example)
    input_pattern = str(frames_dir / pattern)
    # Alternative: if pattern didn't work, use generic
    if "%04d" not in input_pattern:
        input_pattern = str(frames_dir / "frame_%04d.png")

    cmd_master = [ffmpeg, "-y", "-framerate", str(fps), "-i", input_pattern, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(master)]
    # Check for audio to mux
    vo_candidates = [film_dir / "audio" / "vo.wav", film_dir / "audio" / "vo.mp3"]
    vo = next((p for p in vo_candidates if p.exists()), None)
    if vo:
        # mux audio (shortest)
        cmd_master = [ffmpeg, "-y", "-framerate", str(fps), "-i", input_pattern, "-i", str(vo), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-shortest", str(master)]

    print("Encoding master:", " ".join(cmd_master))
    res = subprocess.run(cmd_master, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr[-2000:])
    else:
        print(f"Wrote master {master}")

    # Step 2: derivatives via crop (no re-render) — centered crop
    # Use ffmpeg crop filter: crop=w:h:x:y
    crops = {
        "9:16": 'crop=1080:1920:(in_w-out_w)/2:0',
        "1:1": 'crop=1080:1080:(in_w-out_w)/2:(in_h-out_h)/2',
    }
    for asp in aspects:
        if asp == "16:9":
            continue
        out = output_dir / f"{asp.replace(':','x')}.mp4"
        vf = crops.get(asp)
        if not vf or not master.exists():
            continue
        cmd = [ffmpeg, "-y", "-i", str(master), "-vf", vf, "-c:a", "copy", str(out)]
        # if no audio stream, drop -c:a copy
        if vo is None:
            cmd = [ffmpeg, "-y", "-i", str(master), "-vf", vf, str(out)]
        print(f"Exporting {asp}: {' '.join(cmd)}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-1000:])

    return {"master": str(master), "aspects": aspects}
