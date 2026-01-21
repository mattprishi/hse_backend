from typing import Generator
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture
def app_client() -> Generator[TestClient, None, None]:
    return TestClient(app)


