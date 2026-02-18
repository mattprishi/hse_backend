# HW4: Async Moderation with Kafka

Асинхронная обработка объявлений через Kafka с поддержкой DLQ и retry механизма.

## Setup

### 1. Start infrastructure

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL на порту 5433
- Redpanda (Kafka) на порту 9092
- Redpanda Console на http://localhost:8080

### 2. Run migrations

```bash
psql -d moderation -U user -h localhost -p 5433 -f migrations/V01__init_schema.sql
psql -d moderation -U user -h localhost -p 5433 -f migrations/V02__moderation_results.sql
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

**Response (pending):**
```json
{
  "task_id": 123,
  "status": "pending",
  "is_violation": null,
  "probability": null
}
```

**Response (completed):**
```json
{
  "task_id": 123,
  "status": "completed",
  "is_violation": true,
  "probability": 0.87
}
```

**Response (failed):**
```json
{
  "task_id": 123,
  "status": "failed",
  "is_violation": null,
  "probability": null,
  "error": "Error message"
}
```

## Architecture

- **Kafka Producer**: Отправка задач модерации в очередь
- **Kafka Consumer (Worker)**: Асинхронная обработка задач
- **DLQ**: Обработка ошибок через Dead Letter Queue
- **Retry**: Автоматические повторы при временных ошибках (до 3 попыток)
- **Polling API**: Клиент проверяет статус через GET /moderation_result/{task_id}

## Kafka Topics

- `moderation` - основная очередь задач
- `moderation_dlq` - очередь для ошибок

## Run Tests

```bash
pytest tests/ -v
```
