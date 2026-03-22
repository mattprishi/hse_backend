import os

# Дефолт совпадает с hw8/docker-compose.yml (postgres:5435 -> БД hw)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:5435/hw",
)

MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")

# MLflow Model Registry (docker-compose сервис mlflow на :5000)
USE_MLFLOW = os.getenv("USE_MLFLOW", "false").lower() == "true"
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "moderation_model")
MLFLOW_MODEL_URI = os.getenv(
    "MLFLOW_MODEL_URI",
    f"models:/{MLFLOW_MODEL_NAME}/latest",
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30

WORKER_MAX_RETRIES = int(os.getenv("WORKER_MAX_RETRIES", "3"))
WORKER_RETRY_BASE_DELAY_SEC = float(os.getenv("WORKER_RETRY_BASE_DELAY_SEC", "1.0"))

# DEBUG / INFO / WARNING — для API и воркера
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
