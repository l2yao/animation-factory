# Colab Setup

Bypasses local GTX 650 Ti 1GB / Blender launch failure (exit -1073741502 on driver 456.71).

- `setup.sh` — installs Blender 4.5 LTS (default) or 5.2 to `/opt/blender`, `ffmpeg`, and `factory` pip package. Run via `!bash colab/setup.sh` in Colab.
- `presets/render_colab.yaml` — GPU tier for T4/A100 (EEVEE 64 or CYCLES 128 + CUDA).

Env override: `BLENDER_VERSION=5.2.0 bash colab/setup.sh` or `BLENDER_PATH=/opt/blender/blender`.

See `notebooks/colab_render.ipynb` for full pipeline.
