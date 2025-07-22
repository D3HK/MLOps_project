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

# Копируем всю структуру проекта
COPY src/ ./src/
COPY auth/ ./auth/
COPY dvc.yaml .

RUN mkdir -p /app/data/preprocessed

# Очистка кеша
RUN find /usr/local -type d -name '__pycache__' -exec rm -rf {} + && \
    find /usr/local -name '*.pyc' -delete && \
    find /app -type d -name '__pycache__' -exec rm -rf {} + && \
    find /app -name '*.pyc' -delete

# Указываем PYTHONPATH с учетом новой структуры
ENV PYTHONPATH=/app:/app/src:/app/auth \
    MLFLOW_TRACKING_URI=http://mlflow:5000 \
    PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]