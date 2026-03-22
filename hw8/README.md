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
python3 -m pip install -r requirements.txt
```

### 4. Модель ML (артефакт `model.pkl`)

API и воркер **только загружают** файл по `MODEL_PATH`, обучение при старте не выполняется.

```bash
make train-model
# или: python3 train_model.py
```

### 5. Данные в БД (для `/simple_predict`, k6, Grafana)

После миграций создайте аккаунт и при необходимости пользователя с объявлением:

```bash
python3 create_account.py loadtest loadtest
python3 create_user_and_ad.py
```

Сохраните cookie после логина (для ручных запросов):

```bash
curl -c cookies.txt -X POST http://localhost:8003/login \
  -H "Content-Type: application/json" \
  -d '{"login":"loadtest","password":"loadtest"}'
```

### 6. Переменные (опционально)

Дефолты в `config.py`: `DATABASE_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `REDIS_*`, `MODEL_PATH`, `LOG_LEVEL`.

### 7. API и воркер

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

### Нагрузочный сценарий (k6) и артефакты метрик

**k6 не из pip** — это отдельная программа. На macOS с Homebrew:

```bash
brew install k6
k6 version
```

Иначе: [установка k6](https://grafana.com/docs/k6/latest/set-up/install-k6/) (бинарник под вашу ОС).

Скрипт `load_test.js` сначала логинится (`LOGIN` / `PASSWORD`), затем вызывает `/simple_predict` с cookie — так наполняется `predictions_total` в Prometheus.

Из каталога `hw8` (подставьте `ITEM_ID` из вывода `create_user_and_ad.py`):

```bash
k6 run -e BASE_URL=http://localhost:8003 \
  -e LOGIN=loadtest -e PASSWORD=loadtest -e ITEM_ID=1 \
  load_test.js
```

После прогона: Prometheus `http://localhost:9090`, Grafana → панели с `predictions_total` и др.

## API Endpoints

### POST /simple_predict

Синхронное предсказание с кэшированием. Нужен cookie `access_token` после `POST /login`.

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

Сначала инфраструктура и миграции (схема БД нужна и для интеграционных тестов):

```bash
make up && make migrate
```

Юнит-тесты (без PostgreSQL/Redis):

```bash
make test-unit
```

Все тесты, включая интеграционные:

```bash
make test
```



(venv) user@LW14NF225T-MBP hw8 % k6 run -e BASE_URL=http://localhost:8003 \
  -e LOGIN=loadtest -e PASSWORD=loadtest -e ITEM_ID=10 \
  load_test.js

         /\      Grafana   /‾‾/  
    /\  /  \     |\  __   /  /   
   /  \/    \    | |/ /  /   ‾‾\ 
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/ 


     execution: local
        script: load_test.js
        output: -

     scenarios: (100.00%) 1 scenario, 10 max VUs, 1m0s max duration (incl. graceful stop):
              * default: 10 looping VUs for 30s (gracefulStop: 30s)



  █ TOTAL RESULTS 

    HTTP
    http_req_duration..............: avg=11ms   min=718µs  med=6.4ms   max=166.61ms p(90)=18.86ms p(95)=22.34ms
      { expected_response:true }...: avg=22.2ms min=5.35ms med=16.48ms max=166.61ms p(90)=24.83ms p(95)=83.7ms 
    http_req_failed................: 64.83% 590 out of 910
    http_reqs......................: 910    29.336154/s

    EXECUTION
    iteration_duration.............: avg=1.03s  min=1.01s  med=1.02s   max=1.22s    p(90)=1.03s   p(95)=1.09s  
    iterations.....................: 300    9.67126/s
    vus............................: 10     min=10         max=10
    vus_max........................: 10     min=10         max=10

    NETWORK
    data_received..................: 165 kB 5.3 kB/s
    data_sent......................: 114 kB 3.7 kB/s




running (0m31.0s), 00/10 VUs, 300 complete and 0 interrupted iterations
default ✓ [======================================] 10 VUs  30s