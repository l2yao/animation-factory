import shutil
import subprocess
from pathlib import Path

def _find_blender():
    import glob, os
    candidates = []
    # 1. PATH
    which = shutil.which("blender")
    if which:
        candidates.append(which)
    # 2. Colab / Linux paths
    candidates += [
        "/opt/blender/blender",
        "/usr/local/bin/blender",
        "/usr/bin/blender",
        "./blender/blender",
        "./blender-4.5/blender",
        "/content/blender/blender",
    ]
    # 3. Windows common paths — check newest first, glob fallback
    candidates += [
        r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    ]
    candidates += glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe")
    # 4. Env override
    env_blender = os.environ.get("BLENDER_PATH")
    if env_blender:
        candidates.insert(0, env_blender)
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None

def run(film_dir: Path, config: dict, dry_run: bool = False):
    film_dir = Path(film_dir)
    blend = film_dir / "scenes" / "shot_animated.blend"
    if not blend.exists():
        blend = film_dir / "scenes" / "shot_master.blend"
    out_dir = film_dir / "render" / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)

    blender = _find_blender()
    # Build command (EEVEE, old NVIDIA safe)
    cmd = None
    if blend.exists() and blender:
        # Use blender -b <blend> -a  (render animation) or frame range
        # We render to out_dir via blend settings; ensure --render-output override not needed
        cmd = [blender, "-b", str(blend), "-a"]
    elif blender:
        # fallback: try building first then render
        build_script = film_dir / "scripts" / "build_scene.py"
        if build_script.exists():
            cmd = [blender, "-b", "-P", str(build_script)]
        else:
            cmd = None
    else:
        cmd = None

    if dry_run:
        print(f"[dry-run] renderer: blender={blender}, blend={blend}, out={out_dir}")
        if cmd:
            print("Would run:", " ".join(f'"{c}"' if " " in c else c for c in cmd))
        else:
            print("No Blender found — would simulate render by creating placeholder frames")
        return {"blender": blender, "blend": str(blend), "cmd": cmd, "dry_run": True}

    if not blender:
        # Simulate: create 3 placeholder pngs + info txt
        print("Blender not found — creating placeholder render outputs (install Blender for real render)")
        info = out_dir / "_RENDER_INFO.txt"
        info.write_text(f"No Blender at {blender}. Placeholder for {film_dir.name}.\nInstall Blender 4.2 LTS, then re-run: factory generate --film {film_dir.name} --step render\n", encoding="utf-8")
        # Create a tiny 1x1 png via python if PIL available? Just txt.
        return {"blender": None, "placeholder": str(info)}

    print(f"Rendering with: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr[-2000:])
        return {"blender": blender, "returncode": result.returncode}
    except Exception as e:
        print(f"Render failed: {e}")
        return {"error": str(e)}
