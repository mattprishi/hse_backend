# Сервис модерации объявлений

Один сервис на FastAPI: синхронное и асинхронное предсказание, PostgreSQL, Kafka, Redis, метрики, JWT. Модель — `LogisticRegression`, признаки те же, что и в курсе.

## Быстрый старт

1. Поднять инфраструктуру и применить миграции:

```bash
cd hw8
make up
make migrate
```

2. Установить зависимости:

```bash
python3 -m pip install -r requirements.txt
```

3. Обучить модель и сохранить `model.pkl` (вариант по умолчанию, без MLflow):

```bash
make train-model
```

4. Создать пользователя для логина и тестовые данные в БД:

```bash
python3 create_account.py loadtest loadtest
python3 create_user_and_ad.py
```

Запомните `item_id` объявления из вывода скрипта.

5. Запустить API и воркер (в двух терминалах):

```bash
make run
# другой терминал:
make worker
```

API: http://localhost:8003 · метрики: http://localhost:8003/metrics  
Grafana: http://localhost:3000 (логин/пароль по умолчанию `admin` / `admin`)  
Prometheus: http://localhost:9090

---

## MLflow

В `docker-compose` есть сервис mlflow на порту 5000. UI: http://localhost:5000

Вариант A — только файл `model.pkl` (как сейчас по умолчанию)  
Ничего не меняем: `USE_MLFLOW` не задан или `false`, модель читается с диска.

Вариант B — модель из MLflow Registry

1. Убедитесь, что контейнер mlflow запущен (`make up`).
2. Зарегистрируйте модель:

```bash
make train-model-mlflow
```

3. Запускайте API и воркер с переменными:

```bash
export USE_MLFLOW=true
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
# при необходимости: MLFLOW_MODEL_URI=models:/moderation_model/latest
make run
```

Тот же `USE_MLFLOW` нужен и для `make worker`.

---

## Основные ручки

| Метод | Путь | Описание |
|--------|------|----------|
| POST | `/login` | Выдаёт JWT в cookie `access_token` |
| POST | `/predict` | Предсказание по переданным полям (без БД), нужен JWT |
| POST | `/simple_predict` | Предсказание по `item_id` из БД + Redis-кэш, нужен JWT |
| POST | `/async_predict` | Постановка задачи в Kafka |
| GET | `/moderation_result/{task_id}` | Статус задачи |
| POST | `/close` | Закрыть объявление, сброс кэша и связанных результатов модерации |

Пример `/predict` после логина (cookie):

```bash
curl -c cookies.txt -b cookies.txt -X POST http://localhost:8003/login \
  -H "Content-Type: application/json" \
  -d '{"login":"loadtest","password":"loadtest"}'

curl -b cookies.txt -X POST http://localhost:8003/predict \
  -H "Content-Type: application/json" \
  -d '{"seller_id":1,"is_verified_seller":true,"item_id":1,"name":"x","description":"текст объявления","category":50,"images_qty":3}'
```

---

## Нагрузка (k6)

```bash
k6 run -e BASE_URL=http://localhost:8003 \
  -e LOGIN=loadtest -e PASSWORD=loadtest -e ITEM_ID=<ваш_item_id> \
  load_test.js
```

Часть ответов 404 в сценарии намеренная — у k6 может быть высокий `http_req_failed`, это норм.

---

## Тесты

Нужны поднятый стек и миграции: `make up && make migrate`.

```bash
make test-unit    # без интеграции с БД/Redis
make test         # всё, включая @pytest.mark.integration
```
