import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user@localhost:5432/moderation"
)

MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")
