import logging
import pickle

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
