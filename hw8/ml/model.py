import logging
import pickle
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


def train_model():
    """Обучает простую модель на синтетических данных."""
    np.random.seed(42)
    X = np.random.rand(1000, 4)
    y = (X[:, 0] < 0.3) & (X[:, 1] < 0.2)
    y = y.astype(int)
    model = LogisticRegression()
    model.fit(X, y)
    return model


def save_model(model, path: str) -> None:
    with open(path, "wb") as f:
        pickle.dump(model, f)
    logger.info("Model saved to %s", path)


def load_model(path: str):
    """Загрузка артефакта. API и воркер вызывают только это — без обучения при старте."""
    with open(path, "rb") as f:
        model = pickle.load(f)
    logger.info("Model loaded from %s", path)
    return model


def load_model_from_mlflow(tracking_uri: str, model_uri: str) -> Any:
    """Загрузка sklearn-модели из MLflow Model Registry."""
    import mlflow

    mlflow.set_tracking_uri(tracking_uri)
    model = mlflow.sklearn.load_model(model_uri)
    logger.info("Model loaded from MLflow: %s @ %s", model_uri, tracking_uri)
    return model


def load_inference_model() -> Any:
    """Источник модели: MLflow (USE_MLFLOW=true) или локальный pickle."""
    from config import USE_MLFLOW, MODEL_PATH, MLFLOW_TRACKING_URI, MLFLOW_MODEL_URI

    if USE_MLFLOW:
        return load_model_from_mlflow(MLFLOW_TRACKING_URI, MLFLOW_MODEL_URI)
    try:
        return load_model(MODEL_PATH)
    except FileNotFoundError:
        logger.error(
            "Файл модели не найден: %s. Запустите: python3 train_model.py",
            MODEL_PATH,
        )
        raise


def build_feature_row(
    is_verified_seller: bool,
    images_qty: int,
    description: str,
    category: int,
) -> np.ndarray:
    """Те же признаки, что и для объявления из БД (4 float)."""
    return np.array(
        [
            [
                1.0 if is_verified_seller else 0.0,
                images_qty / 10.0,
                len(description) / 1000.0,
                category / 100.0,
            ]
        ]
    )


def train_and_save(path: str):
    """Обучение и сохранение в файл (скрипт train_model.py, тесты)."""
    model = train_model()
    save_model(model, path)
    return model


def load_or_train_model(path: str):
    """Только для тестов/локальной отладки: нет файла — обучить и сохранить."""
    try:
        return load_model(path)
    except FileNotFoundError:
        logger.info("Model not found at %s, training new model for tests", path)
        return train_and_save(path)
