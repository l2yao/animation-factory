import shutil
import subprocess
from pathlib import Path

def _find_blender():
    import os
    candidates = []
    # Env override first (Colab: BLENDER_PATH=/opt/blender/blender)
    env_blender = os.environ.get("BLENDER_PATH", "/opt/blender/blender")
    if env_blender:
        candidates.append(env_blender)
    # PATH
    which = shutil.which("blender")
    if which:
        candidates.append(which)
    # Colab / Linux paths
    candidates += [
        "/opt/blender/blender",
        "/usr/local/bin/blender",
        "/usr/bin/blender",
    ]
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
    # Build command (Colab GPU, Blender 5.x EEVEE_NEXT)
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
        print("Blender not found — render on Colab GPU (see notebooks/colab_render.ipynb).")
        info = out_dir / "_RENDER_INFO.txt"
        info.write_text(f"No Blender at {blender}. Placeholder for {film_dir.name}.\nRun on Colab: factory generate --film {film_dir.name} --step render\n", encoding="utf-8")
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
