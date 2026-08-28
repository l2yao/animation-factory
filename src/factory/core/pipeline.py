from pathlib import Path
from .config import load_film_config, get_film_dir
from ..adapters import parse as parse_adapter, bpy_scene, renderer, tts, ffmpeg_export

STEPS = ["parse", "build", "animate", "render", "audio", "export"]

def run_pipeline(film: str, steps=None, dry_run: bool = False, aspects=None):
    film_dir = get_film_dir(film)
    if not film_dir.exists():
        raise FileNotFoundError(f"Film dir not found: {film_dir}")
    config = load_film_config(film_dir)
    steps = steps or STEPS
    if isinstance(steps, str):
        steps = [steps]
    # filter to known
    steps = [s for s in steps if s in STEPS]
    results = {}
    for step in steps:
        print(f"\n==> Step: {step} (dry_run={dry_run})")
        if step == "parse":
            results[step] = parse_adapter.run(film_dir, config, dry_run=dry_run)
        elif step == "build":
            results[step] = bpy_scene.run(film_dir, config, dry_run=dry_run, mode="build")
        elif step == "animate":
            results[step] = bpy_scene.run(film_dir, config, dry_run=dry_run, mode="animate")
        elif step == "render":
            results[step] = renderer.run(film_dir, config, dry_run=dry_run)
        elif step == "audio":
            results[step] = tts.run(film_dir, config, dry_run=dry_run)
        elif step == "export":
            results[step] = ffmpeg_export.run(film_dir, config, dry_run=dry_run, aspects=aspects)
    print("\nPipeline done:", results)
    return results
