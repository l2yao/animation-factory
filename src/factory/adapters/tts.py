from pathlib import Path
import json
import shutil
import subprocess

def _find_piper():
    return shutil.which("piper") or shutil.which("piper.exe")

def _find_ffmpeg():
    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")

def run(film_dir: Path, config: dict, dry_run: bool = False):
    film_dir = Path(film_dir)
    shots_path = film_dir / "shots.json"
    audio_dir = film_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    if not shots_path.exists():
        print(f"No shots.json at {shots_path} — run parse first")
        return {"error": "no shots.json"}

    data = json.loads(shots_path.read_text(encoding="utf-8"))
    shots = data.get("shots", [])
    full_text = " ".join([s.get("narration", "") for s in shots]).strip()
    if not full_text:
        full_text = "Welcome to our Pixar style story."

    out_wav = audio_dir / "vo.wav"
    concat_txt = audio_dir / "_vo_concat.txt"

    piper = _find_piper()
    ffmpeg = _find_ffmpeg()

    if dry_run:
        print(f"[dry-run] tts: text_len={len(full_text)}, piper={piper}, ffmpeg={ffmpeg}, out={out_wav}")
        print(f"Text preview: {full_text[:180]}...")
        return {"piper": piper, "out": str(out_wav), "dry_run": True}

    # If Piper available, use it; else fallback to gTTS/file or placeholder
    if piper:
        # Piper needs model; we attempt default voice
        # Factory ships without model — user must download en_US-ryan-medium.onnx
        model = config.get("audio", {}).get("voice_model", "en_US-ryan-medium.onnx")
        model_path = Path(model)
        if not model_path.exists():
            # look in assets_library
            alt = Path(__file__).resolve().parents[3] / "assets_library" / model
            if alt.exists():
                model_path = alt
        if model_path.exists():
            cmd = [piper, "--model", str(model_path), "--output_file", str(out_wav)]
            proc = subprocess.run(cmd, input=full_text.encode("utf-8"), capture_output=True)
            print(proc.stdout.decode(errors="ignore")[-500:])
            if proc.returncode == 0 and out_wav.exists():
                print(f"Piper TTS wrote {out_wav}")
                return {"out": str(out_wav)}
        print(f"Piper found but model missing at {model_path} — creating placeholder. Download Piper voice to enable.")
    
    # Fallback: try gTTS if installed
    try:
        from gtts import gTTS
        tts = gTTS(full_text[:4000], lang='en')
        tts.save(str(out_wav.with_suffix(".mp3")))
        print(f"gTTS fallback wrote {out_wav.with_suffix('.mp3')}")
        return {"out": str(out_wav.with_suffix(".mp3")), "engine": "gtts"}
    except Exception as e:
        print(f"gTTS not available: {e}")

    # Final fallback: create silent wav placeholder via ffmpeg if available
    if ffmpeg:
        #  duration estimate: word count * 0.4 + shots overhead
        words = len(full_text.split())
        dur = max(5, min(120, words * 0.4 + len(shots)*0.5))
        cmd = [ffmpeg, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(round(dur,1)), str(out_wav)]
        subprocess.run(cmd, capture_output=True)
        if out_wav.exists():
            print(f"Created silent placeholder VO {out_wav} ({dur}s) — replace with Piper/human VO")
            return {"out": str(out_wav), "placeholder": True, "duration": dur}

    # Last resort: txt
    txt = audio_dir / "vo.txt"
    txt.write_text(full_text, encoding="utf-8")
    print(f"No TTS engine — wrote {txt} (add Piper or record human VO)")
    return {"out": str(txt), "placeholder": True}
