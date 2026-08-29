#!/usr/bin/env bash
set -e
# Colab setup: download Blender 4.5 LTS (or 5.2) + install factory
# Usage on Colab: !bash colab/setup.sh  OR  !bash /content/animation-factory/colab/setup.sh

BLENDER_VERSION=${BLENDER_VERSION:-4.5.2}
# Use 4.5 LTS for stability; override with BLENDER_VERSION=5.2.0 for latest
if [[ "$BLENDER_VERSION" == 5.* ]]; then
  BLENDER_URL="https://download.blender.org/release/Blender${BLENDER_VERSION%.*}/blender-${BLENDER_VERSION}-linux-x64.tar.xz"
else
  BLENDER_URL="https://download.blender.org/release/Blender${BLENDER_VERSION%.*}/blender-${BLENDER_VERSION}-linux-x64.tar.xz"
fi

echo "-> Checking Blender at /opt/blender/blender"
if [ -x "/opt/blender/blender" ]; then
  echo "Blender already installed: $(/opt/blender/blender --version | head -n1)"
else
  echo "-> Downloading Blender $BLENDER_VERSION from $BLENDER_URL"
  mkdir -p /opt/blender
  # try wget, fallback to curl
  if command -v wget >/dev/null; then
    wget -q --show-progress -O /tmp/blender.tar.xz "$BLENDER_URL"
  else
    curl -L -o /tmp/blender.tar.xz "$BLENDER_URL"
  fi
  tar -xf /tmp/blender.tar.xz -C /opt --strip-components=1 --exclude="blender-*/3.6/datafiles" || tar -xf /tmp/blender.tar.xz -C /opt/blender --strip-components=1
  # ensure binary is at /opt/blender/blender
  if [ ! -f "/opt/blender/blender" ] && [ -f "/opt/blender-*/blender" ]; then
    mv /opt/blender-*/* /opt/blender/ 2>/dev/null || true
  fi
  chmod +x /opt/blender/blender
  echo "-> Blender installed: $(/opt/blender/blender --version | head -n1)"
fi

echo "-> Checking ffmpeg"
if ! command -v ffmpeg >/dev/null; then
  apt-get update -qq && apt-get install -y ffmpeg >/dev/null
fi
ffmpeg -version | head -n1

echo "-> Installing animation-factory"
if [ -f "/content/animation-factory/pyproject.toml" ]; then
  pip install -q -e /content/animation-factory
else
  echo "Run from repo root or colab will clone below"
fi

echo "-> Colab setup done. Test: factory --help ; /opt/blender/blender --version"
