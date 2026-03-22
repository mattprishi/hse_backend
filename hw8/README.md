# Модерация объявлений (hw8)

## Запуск (как в hw6: один compose + Makefile)

### 1. Инфраструктура

```bash
make up
```

Поднимется: PostgreSQL **5435** (БД `hw`), Redis **6379**, Redpanda (Kafka) **9092**, Redpanda Console **8080**, Prometheus **9090**, Grafana **3000** (admin / admin).

### 2. Миграции

```bash
make migrate
```

(нужен `psql` в PATH; `DATABASE_URL` можно не задавать — см. `Makefile`)

### 3. Зависимости

```bash
pip install -r requirements.txt
```

### 4. Переменные (опционально)

Дефолты совпадают с `config.py`: `DATABASE_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `REDIS_*`, `MODEL_PATH`, `LOG_LEVEL`.

### 5. API и воркер

Терминал 1 — API (**:8003**):

```bash
make run
```

Терминал 2 — воркер Kafka:

```bash
make worker
```

- Метрики API: `http://localhost:8003/metrics` (Prometheus в Docker скрейпит `host.docker.internal:8003`).
- Grafana: `http://localhost:3000`, дашборды из `grafana/dashboards/`.

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

## Тесты

```bash
make test-unit    # без Docker
make test         # нужны make up && make migrate
```
