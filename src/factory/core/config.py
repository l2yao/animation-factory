import yaml
import json
from pathlib import Path
from dataclasses import dataclass, field

DEFAULT_ROOT = Path(__file__).resolve().parents[3]  # animation-factory/
PRESET_DIR = DEFAULT_ROOT / "presets"

def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def deep_merge(a: dict, b: dict) -> dict:
    """Merge b into a (b wins)."""
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def resolve_preset(preset_name: str) -> dict:
    # Try pixar.yaml or <name>.yaml
    candidates = [PRESET_DIR / f"{preset_name}.yaml", PRESET_DIR / f"render_{preset_name}.yaml"]
    # Also allow direct path
    p = Path(preset_name)
    if p.exists():
        candidates.insert(0, p)
    for c in candidates:
        if c.exists():
            return load_yaml(c)
    # fallback: pixar
    fallback = PRESET_DIR / "pixar.yaml"
    if fallback.exists():
        return load_yaml(fallback)
    return {}

def load_film_config(film_dir: Path) -> dict:
    import os
    cfg_path = film_dir / "config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"config.yaml not found in {film_dir}")
    cfg = load_yaml(cfg_path)
    # merge presets
    preset_name = cfg.get("preset", cfg.get("style_preset", "pixar"))
    preset = resolve_preset(preset_name)
    # Auto-pick render tier: Colab GPU vs old local NVIDIA
    render_preset_name = cfg.get("render_preset")
    if not render_preset_name:
        # Detect Colab (has COLAB_GPU or COLAB_RELEASE_TAG) or Linux with GPU
        if os.environ.get("COLAB_RELEASE_TAG") or os.environ.get("COLAB_GPU") or Path("/opt/blender/blender").exists():
            render_preset_name = "render_colab"
        else:
            render_preset_name = "render_old_nvidia"
    render_preset = resolve_preset(render_preset_name)
    merged = deep_merge(render_preset, preset)
    merged = deep_merge(merged, cfg)
    # Normalize aspects
    if "aspects" not in merged and "render" in merged and "aspects" in merged["render"]:
        merged["aspects"] = merged["render"]["aspects"]
    return merged

def get_film_dir(name_or_path: str) -> Path:
    p = Path(name_or_path)
    if p.exists() and (p / "config.yaml").exists():
        return p.resolve()
    # Try films/<name>
    candidate = DEFAULT_ROOT / "films" / name_or_path
    if candidate.exists():
        return candidate.resolve()
    return candidate.resolve()
