import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user@localhost:5433/moderation"
)

MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
