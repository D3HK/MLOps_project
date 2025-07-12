# Этап сборки с временными зависимостями
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --prefix=/install --no-cache-dir -r requirements.txt dvc

# Финальный этап
FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /install /usr/local

RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY api.py .
COPY src/models/ src/models/
COPY src/data/ src/data/
COPY data/preprocessed/ data/preprocessed/
COPY dvc.yaml .
COPY auth/ auth/
COPY database.py .
RUN apt-get update && apt-get install -y curl

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    find /usr/local -type d -name '__pycache__' -exec rm -rf {} + && \
    find /usr/local -name '*.pyc' -delete

ENV PYTHONPATH=/app \
    MLFLOW_TRACKING_URI=http://mlflow:5000 \
    PYTHONUNBUFFERED=1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]