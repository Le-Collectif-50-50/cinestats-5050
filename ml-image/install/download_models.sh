#!/bin/bash
set -euo pipefail


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$ROOT_DIR/models"

mkdir -p "$MODELS_DIR"

echo "Les modeles seront dans $MODELS_DIR"


if ! command -v gdown &> /dev/null; then
    echo "Installation de gdown..."
    pip install gdown
fi


YOLO_MODEL="$MODELS_DIR/yolov11n-face.pt"
if [ ! -f "$YOLO_MODEL" ]; then
    curl --fail --location -o "$YOLO_MODEL.part" https://github.com/akanametov/yolo-face/releases/download/1.0.0/yolov11n-face.pt
    mv "$YOLO_MODEL.part" "$YOLO_MODEL"
    echo "Téléchargement terminé."
else
    echo "$YOLO_MODEL déjà présent, téléchargement ignoré."
fi

FAIR_MODEL="$MODELS_DIR/res34_fair_align_multi_7_20190809.pt"
if [ ! -f "$FAIR_MODEL" ]; then
    gdown 113QMzQzkBDmYMs9LwzvD-jxEZdBQ5J4X -O "$FAIR_MODEL.part"
    mv "$FAIR_MODEL.part" "$FAIR_MODEL"
    echo "Téléchargement terminé."
else
    echo "$FAIR_MODEL déjà présent, téléchargement ignoré."
fi
