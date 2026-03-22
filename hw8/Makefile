# Поднять Postgres, Redis, Kafka (Redpanda)
up:
	docker-compose up -d

down:
	docker-compose down

# Применить миграции (после up)
migrate:
	export DATABASE_URL="postgresql://postgres:postgres@localhost:5435/hw" && \
	for f in migrations/V*.sql; do psql "$$DATABASE_URL" -f $$f; done

# Юнит-тесты без БД/Redis/Kafka
test-unit:
	pytest -m "not integration" -v

# Все тесты (нужны: docker-compose up)
test:
	export DATABASE_URL="postgresql://postgres:postgres@localhost:5435/hw" && pytest -v

# Запуск приложения (нужны: up + migrate)
run:
	export DATABASE_URL="postgresql://postgres:postgres@localhost:5435/hw" && python main.py
