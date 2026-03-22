#!/usr/bin/env python3
"""Обучение модели, сохранение в pickle и (опционально) регистрация в MLflow.

Без MLflow: только файл model.pkl
С MLflow: задайте MLFLOW_TRACKING_URI (например http://127.0.0.1:5000), см. README.
"""
from __future__ import annotations

import os
import sys

from config import MLFLOW_MODEL_NAME, MODEL_PATH
from ml.model import save_model, train_model


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else MODEL_PATH
    model = train_model()
    save_model(model, path)
    print(f"Модель сохранена: {path}")

    tracking = os.getenv("MLFLOW_TRACKING_URI")
    if not tracking:
        print("MLflow пропущен (не задан MLFLOW_TRACKING_URI).")
        return

    import mlflow
    import mlflow.sklearn

    model_name = os.getenv("MLFLOW_MODEL_NAME", MLFLOW_MODEL_NAME)
    mlflow.set_tracking_uri(tracking)
    with mlflow.start_run():
        mlflow.sklearn.log_model(
            model,
            artifact_path="sklearn-model",
            registered_model_name=model_name,
        )
    print(f"MLflow: зарегистрирована модель «{model_name}» → models:/{model_name}/latest")


if __name__ == "__main__":
    main()
