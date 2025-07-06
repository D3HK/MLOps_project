#!/bin/bash

echo "Waiting for MLflow to be ready..."
while ! curl -s http://mlflow:5000 >/dev/null; do
  sleep 1
done

if [ ! -f "src/models/trained_model.joblib" ]; then
  echo "Model not found, running training pipeline..."
  dvc repro train
fi

echo "Starting API server..."
exec uvicorn api:app --host 0.0.0.0 --port 8000