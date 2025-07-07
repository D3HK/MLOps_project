#!/bin/bash
set -e

PROJECT_ROOT="/Users/Denis/Desktop/PROJECT/MLOps_accidents"  
cd "$PROJECT_ROOT" || { echo "Ошибка перехода в $PROJECT_ROOT"; exit 1; }

if [ ! -d .dvc ]; then
    echo "ERROR: .dvc directory not found!" >&2
    exit 1
fi

dvc repro evaluate --force

echo "[$(date)] Retraining completed" >> "$PROJECT_ROOT/retrain.log"