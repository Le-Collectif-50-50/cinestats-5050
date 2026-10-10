#!/usr/bin/env bash
# Environnement isolé pour les tests CPU locaux (Python 3.11).
set -euo pipefail
ML_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v uv >/dev/null || { echo "Installer uv avant de continuer." >&2; exit 1; }
command -v c++ >/dev/null || { echo "Compilateur C++ requis pour dlib." >&2; exit 1; }
uv venv "$ML_ROOT/.venv" --python 3.11 --allow-existing
uv pip install --python "$ML_ROOT/.venv/bin/python" 'cmake==3.31.6' 'gdown==5.2.0'
export PATH="$ML_ROOT/.venv/bin:$PATH"
uv pip install --python "$ML_ROOT/.venv/bin/python" -r "$ML_ROOT/requirements-local.txt"
cd "$ML_ROOT"
export XDG_CACHE_HOME="$ML_ROOT/tmp/cache"
export MPLCONFIGDIR="$ML_ROOT/tmp/matplotlib"
export YOLO_CONFIG_DIR="$ML_ROOT/tmp/ultralytics"
mkdir -p "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"
.venv/bin/python main.py --help
.venv/bin/python -m unittest discover -s tests -v
