import click
import shutil
from pathlib import Path
import yaml

from .core.config import DEFAULT_ROOT, get_film_dir, load_film_config
from .core.pipeline import run_pipeline, STEPS

@click.group()
@click.version_option(version="0.1.0")
def main():
    """Animation Factory — reusable Pixar-style 3D pipeline"""
    pass

@main.command("new-film")
@click.option("--name", required=True, help="Film folder name (e.g., my-film-001)")
@click.option("--input", "input_path", required=False, help="Path to source text file or inline text")
@click.option("--preset", default="pixar", help="Style preset (pixar)")
@click.option("--render-preset", default=None, help="Render tier: render_old_nvidia (GTX 650 Ti) or render_colab (T4/A100)")
@click.option("--duration", type=int, default=90, help="Target duration seconds")
@click.option("--force", is_flag=True, help="Overwrite existing film folder")
def new_film(name, input_path, preset, render_preset, duration, force):
    """Scaffold a new film folder under films/<name>"""
    film_dir = DEFAULT_ROOT / "films" / name
    if film_dir.exists() and not force:
        click.echo(f"Film dir already exists: {film_dir} (use --force to overwrite)")
        return
    film_dir.mkdir(parents=True, exist_ok=True)
    (film_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (film_dir / "scenes").mkdir(parents=True, exist_ok=True)
    (film_dir / "render" / "frames").mkdir(parents=True, exist_ok=True)
    (film_dir / "audio").mkdir(parents=True, exist_ok=True)
    (film_dir / "final").mkdir(parents=True, exist_ok=True)

    # Resolve input text
    input_text_val = input_path or ""
    if input_path and Path(input_path).exists():
        # copy input text into film folder for provenance
        src = Path(input_path)
        dst = film_dir / "input.txt"
        shutil.copy2(src, dst)
        click.echo(f"Copied input text: {src} -> {dst}")
        input_text_val = str(dst)
    elif input_path and len(input_path) > 20:
        # treat as inline text -> write to input.txt
        (film_dir / "input.txt").write_text(input_path, encoding="utf-8")
        input_text_val = str(film_dir / "input.txt")
        click.echo(f"Wrote inline text to {film_dir / 'input.txt'}")
    else:
        # create placeholder input.txt
        placeholder = film_dir / "input.txt"
        if not placeholder.exists():
            placeholder.write_text("A small brave character discovers a glowing secret in a cozy Pixar-style town. Through kindness and courage, they share the light with everyone.\n", encoding="utf-8")
        if not input_text_val:
            input_text_val = str(placeholder)

    # render_preset determines engine; don't hardcode EEVEE if Colab preset requested
    render_cfg = {"fps": 24}
    if render_preset == "render_colab":
        render_cfg["engine"] = "BLENDER_EEVEE_NEXT"
    elif render_preset:
        # will be resolved via presets, keep minimal
        pass
    else:
        render_cfg["engine"] = "BLENDER_EEVEE"
    config = {
        "film": name,
        "input_text": input_text_val,
        "preset": preset,
        "duration_target": duration,
        "aspects": ["16:9", "9:16", "1:1"],
        "render": render_cfg
    }
    if render_preset:
        config["render_preset"] = render_preset
    cfg_path = film_dir / "config.yaml"
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)
    click.echo(f"Created film: {film_dir}")
    click.echo(f"  config: {cfg_path}")
    click.echo(f"  Next: factory generate --film {name} --dry-run")
    click.echo(f"        factory generate --film {name}")

@main.command("generate")
@click.option("--film", required=True, help="Film name or path (films/<name>)")
@click.option("--step", type=click.Choice(STEPS), help="Run single step only")
@click.option("--dry-run", is_flag=True, help="Preview without writing/rendering")
@click.option("--aspect", help="Comma-separated aspects to export (16:9,9:16,1:1)")
def generate(film, step, dry_run, aspect):
    """Run pipeline for a film (all steps or single step)"""
    steps = [step] if step else None
    aspects = aspect.split(",") if aspect else None
    run_pipeline(film, steps=steps, dry_run=dry_run, aspects=aspects)

@main.command("render")
@click.option("--film", required=True)
@click.option("--dry-run", is_flag=True)
def render(film, dry_run):
    """Shortcut: factory generate --film <name> --step render"""
    run_pipeline(film, steps=["render"], dry_run=dry_run)

@main.command("list")
def list_films():
    """List all films"""
    films_root = DEFAULT_ROOT / "films"
    if not films_root.exists():
        click.echo("No films folder")
        return
    for p in sorted(films_root.iterdir()):
        if p.is_dir() and (p / "config.yaml").exists():
            cfg = load_film_config(p)
            click.echo(f"- {p.name}: preset={cfg.get('preset')} duration={cfg.get('duration_target')} aspects={cfg.get('aspects')}")

@main.command("info")
@click.option("--film", required=True)
def info(film):
    """Show film config"""
    film_dir = get_film_dir(film)
    cfg = load_film_config(film_dir)
    click.echo(yaml.safe_dump(cfg, sort_keys=False))

if __name__ == "__main__":
    main()
