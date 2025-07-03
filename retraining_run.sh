#!/bin/bash
set -e  # Остановиться при ошибке
cd "$(dirname "$0")"  # Автоматическое определение пути к проекту
dvc repro evaluate