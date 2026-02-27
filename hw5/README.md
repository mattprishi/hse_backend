# HW5: Redis Caching

Кэширование результатов предсказаний с использованием Redis.

## Setup

### 1. Start infrastructure

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL на порту 5433
- Redpanda (Kafka) на порту 9092
- Redpanda Console на http://localhost:8080
- Redis на порту 6379

### 2. Run migrations

```bash
psql -d moderation -U user -h localhost -p 5433 -f migrations/V01__init_schema.sql
psql -d moderation -U user -h localhost -p 5433 -f migrations/V02__moderation_results.sql
psql -d moderation -U user -h localhost -p 5433 -f migrations/V03__add_is_closed.sql
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
export DATABASE_URL="postgresql://user@localhost:5433/moderation"
export MODEL_PATH="model.pkl"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
```

### 5. Run application

Terminal 1 - API server:
```bash
python main.py
```

Terminal 2 - Worker:
```bash
python -m workers.moderation_worker
```

## API Endpoints

### POST /simple_predict

Синхронное предсказание с кэшированием.

**Request:**
```json
{"item_id": 1}
```

**Response:**
```json
{
  "is_violation": true,
  "probability": 0.87
}
```

### POST /async_predict

Создает задачу на асинхронную модерацию.

**Request:**
```
POST /async_predict?item_id=1
```

**Response:**
```json
{
  "task_id": 123,
  "status": "pending",
  "message": "Moderation request accepted"
}
```

### GET /moderation_result/{task_id}

Получает статус модерации.

### POST /close

Закрывает объявление, удаляет из Redis и PostgreSQL.

**Request:**
```json
{"item_id": 1}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Ad 1 closed"
}
```

## Caching Strategy

- **TTL**: 60 секунд (баланс между актуальностью и снижением нагрузки)
- **Pattern**: Cache-Aside (проверка кэша → БД → запись в кэш)
- **Invalidation**: При закрытии объявления

## Run Tests

Все тесты:
```bash
pytest tests/ -v
```

Только интеграционные:
```bash
pytest -m integration -v
```

Только юнит-тесты:
```bash
pytest -m "not integration" -v
```
