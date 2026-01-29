from typing import Generator
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from model import load_or_train_model
from routers.predict import set_model


@pytest.fixture(scope="session")
def trained_model():
    """Загружает модель один раз для всех тестов"""
    return load_or_train_model("model.pkl")


@pytest.fixture
def app_client(trained_model) -> Generator[TestClient, None, None]:
    set_model(trained_model)
    with TestClient(app) as client:
        yield client
