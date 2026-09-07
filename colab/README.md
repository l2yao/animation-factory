# Colab Setup

Render target is Colab GPU (T4/A100).

- `setup.sh` — installs Blender 5.x to `/opt/blender`, `ffmpeg`, and `factory` pip package. Run via `!bash colab/setup.sh` in Colab.
- `presets/render_colab.yaml` — GPU tier for T4/A100 (EEVEE 64 or CYCLES 128 + CUDA).

Env override: `BLENDER_VERSION=5.2.0 bash colab/setup.sh` or `BLENDER_PATH=/opt/blender/blender`.

See `notebooks/colab_render.ipynb` for full pipeline.
