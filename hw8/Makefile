# Единый сценарий как в hw6: инфраструктура + миграции + API/воркер.
# Переменные по умолчанию совпадают с config.py и docker-compose.yml.

SHELL := /bin/bash

export DATABASE_URL ?= postgresql://postgres:postgres@127.0.0.1:5435/hw
export KAFKA_BOOTSTRAP_SERVERS ?= localhost:9092
export REDIS_HOST ?= localhost
export REDIS_PORT ?= 6379
export MODEL_PATH ?= model.pkl
export LOG_LEVEL ?= INFO
# Для USE_MLFLOW=true и train-model-mlflow
export MLFLOW_TRACKING_URI ?= http://127.0.0.1:5000

.PHONY: up down migrate train-model train-model-mlflow run worker test test-unit

# Поднять Postgres, Redis, Redpanda, Console, Prometheus, Grafana
up:
	docker compose up -d

down:
	docker compose down

# Миграции (после up; нужен psql в PATH)
migrate:
	set -e; for f in migrations/V*.sql; do psql "$$DATABASE_URL" -f "$$f"; done

# Обучить и сохранить model.pkl (до make run / make worker)
train-model:
	python3 train_model.py

# То же + регистрация в MLflow (нужен запущенный контейнер mlflow на :5000)
train-model-mlflow:
	MLFLOW_TRACKING_URI=$(MLFLOW_TRACKING_URI) python3 train_model.py

# API на :8003 (нужны: up + migrate + train-model или MLflow)
run:
	python3 main.py

# Воркер модерации (Kafka consumer)
worker:
	python3 -m workers.moderation_worker

# Юнит-тесты без БД/Redis
test-unit:
	python3 -m pytest -m "not integration" -v

# Интеграционные тесты (нужны: make up && make migrate)
test:
	python3 -m pytest -v
