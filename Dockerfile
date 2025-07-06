# Этап сборки зависимостей
FROM python:3.9-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Финальный образ
FROM python:3.9-slim

# Установка curl и зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt \
    && chmod +x startup.sh retraining_run.sh

CMD ["./startup.sh"]