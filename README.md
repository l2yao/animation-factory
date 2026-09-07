# Animation Factory — Reusable Pixar-Style 3D Pipeline

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/l2yao/animation-factory/blob/main/notebooks/colab_render.ipynb)

CLI-driven, config-based factory for generating short 3D animated films from text. **Colab GPU (T4/A100).**

**Hardware:** Colab T4/A100 → full GPU render. Factory targets Blender `5.x` (`BLENDER_EEVEE_NEXT`, fallback to `CYCLES`).

## Quick Start

```bash
pip install -e .
factory --help

# 1. Create reusable film folder from text
factory new-film --name my-film-001 --input path/to/text.txt --preset pixar --duration 90

# 2. Generate full pipeline (parse → build → render → export)
factory generate --film my-film-001

# 3. Or run steps individually
factory generate --film my-film-001 --step parse
factory generate --film my-film-001 --step build
factory generate --film my-film-001 --step render --dry-run
factory generate --film my-film-001 --step export --aspect 9:16
```

## Structure
```
animation-factory/
├── src/factory/          # reusable code (never per-film)
├── presets/              # style + render tiers
├── assets_library/       # shared characters/sets/hdris
├── films/<name>/         # per-film config + outputs
└── tests/
```

## Multi-Aspect Export
Master rendered at 16:9, derivatives via ffmpeg crop with safe-frame (no re-render).

## Colab GPU render

Use free Colab T4:

1. Open `notebooks/colab_render.ipynb` → Runtime → T4 GPU → Run All
2. Edit `YOUR_TEXT` in Cell 2 for any new film — reusable factory
3. Outputs: `films/<name>/final/16x9.mp4` (YouTube) + `9x16` (TikTok) + `1x1` (IG) via `ffmpeg` — no re-render for aspects

Setup script: `colab/setup.sh` installs Blender to `/opt/blender` + `ffmpeg` + `pip install -e .`. See notebook for `render_colab` preset (EEVEE_NEXT 64 samples or `CYCLES` 128 + `CUDA`/`OPTIX`).

## Presets
- `pixar.yaml` — toon Principled BSDF, subsurface, rim light
- `render_colab.yaml` — EEVEE_NEXT/CYCLES, 1080p, 64-128 samples, CUDA/OptiX for T4/A100
