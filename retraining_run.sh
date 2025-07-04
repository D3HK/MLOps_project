#!/bin/bash
set -e  # Остановиться при ошибке
cd /app  # Жёстко задаём путь внутри контейнера
dvc repro evaluate  # Запускаем конкретную стадию пайплайна
echo "[$(date)] Retraining completed successfully" >> /app/retrain.log