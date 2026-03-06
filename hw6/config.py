import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user@localhost:5433/moderation"
)

MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
