# Единый сценарий как в hw6: инфраструктура + миграции + API/воркер.
# Переменные по умолчанию совпадают с config.py и docker-compose.yml.

SHELL := /bin/bash

export DATABASE_URL ?= postgresql://postgres:postgres@127.0.0.1:5435/hw
export KAFKA_BOOTSTRAP_SERVERS ?= localhost:9092
export REDIS_HOST ?= localhost
export REDIS_PORT ?= 6379
export MODEL_PATH ?= model.pkl
export LOG_LEVEL ?= INFO

.PHONY: up down migrate run worker test test-unit

# Поднять Postgres, Redis, Redpanda, Console, Prometheus, Grafana
up:
	docker compose up -d

down:
	docker compose down

# Миграции (после up; нужен psql в PATH)
migrate:
	set -e; for f in migrations/V*.sql; do psql "$$DATABASE_URL" -f "$$f"; done

# API на :8003 (нужны: up + migrate)
run:
	python main.py

# Воркер модерации (Kafka consumer)
worker:
	python -m workers.moderation_worker

# Юнит-тесты без БД/Redis
test-unit:
	pytest -m "not integration" -v

# Интеграционные тесты (нужны: make up && make migrate)
test:
	pytest -v
