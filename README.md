# Animation Factory — Reusable Pixar-Style 3D Pipeline

CLI-driven, config-based factory for generating short 3D animated films from text.

**Hardware profile:** Optimized for old NVIDIA (GTX 650 Ti 1GB) — EEVEE primary, Cycles disabled by default.

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

## Presets
- `pixar.yaml` — toon Principled BSDF, subsurface, rim light
- `render/old-nvidia.yaml` — EEVEE, 1080p, low samples for 1GB VRAM
