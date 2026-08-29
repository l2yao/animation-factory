# Animation Factory — Reusable Pixar-Style 3D Pipeline

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/l2yao/animation-factory/blob/main/notebooks/colab_render.ipynb)

CLI-driven, config-based factory for generating short 3D animated films from text. **Local + Colab GPU.**

**Hardware:** Local GTX 650 Ti 1GB → EEVEE placeholder; **Colab T4/A100 → full GPU render (recommended)**. Factory is Blender-version agnostic — tested with `5.2`, fallback to `4.5 LTS` (4.2 LTS EOL 2026-07).

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

## Colab GPU (bypass old local GPU)

No local Blender? Use free Colab T4:

1. Open `notebooks/colab_render.ipynb` → Runtime → T4 GPU → Run All
2. Edit `YOUR_TEXT` in Cell 2 for any new film — reusable factory
3. Outputs: `films/<name>/final/16x9.mp4` (YouTube) + `9x16` (TikTok) + `1x1` (IG) via `ffmpeg` — no re-render for aspects

Setup script: `colab/setup.sh` installs Blender to `/opt/blender` + `ffmpeg` + `pip install -e .`. See notebook for `render_colab` preset (EEVEE 64 samples or `CYCLES` 128 + `CUDA`/`OPTIX`).

Local alternative (no GPU): `factory generate --film X --step render --dry-run` + placeholders.

## Presets
- `pixar.yaml` — toon Principled BSDF, subsurface, rim light
- `render_old_nvidia.yaml` — EEVEE, 1080p, 16 samples for 1GB VRAM (local GTX 650 Ti)
- `render_colab.yaml` — EEVEE/CYCLES, 1080p, 64-128 samples, CUDA/OptiX for T4/A100
