import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import jwt
from config import JWT_SECRET_KEY, JWT_ALGORITHM
from services.auth import AuthService
from models.entities import Account


@pytest.fixture
def mock_repo():
    r = MagicMock()
    r.get_by_login_and_password = AsyncMock()
    r.get_by_id = AsyncMock()
    return r


@pytest.mark.asyncio
async def test_authenticate_success(mock_repo):
    account = Account(id=1, login="u", password="", is_blocked=False)
    mock_repo.get_by_login_and_password.return_value = account
    svc = AuthService(account_repository=mock_repo)
    result = await svc.authenticate_user("u", "p")
    assert result == account


@pytest.mark.asyncio
async def test_authenticate_wrong_password(mock_repo):
    mock_repo.get_by_login_and_password.return_value = None
    svc = AuthService(account_repository=mock_repo)
    assert await svc.authenticate_user("u", "wrong") is None


@pytest.mark.asyncio
async def test_authenticate_blocked(mock_repo):
    account = Account(id=1, login="u", password="", is_blocked=True)
    mock_repo.get_by_login_and_password.return_value = account
    svc = AuthService(account_repository=mock_repo)
    assert await svc.authenticate_user("u", "p") is None


@pytest.mark.asyncio
async def test_create_and_verify_token(mock_repo):
    svc = AuthService(account_repository=mock_repo)
    token = svc.create_access_token(42)
    assert isinstance(token, str)
    user_id = svc.verify_token(token)
    assert user_id == 42


@pytest.mark.asyncio
async def test_verify_expired_token(mock_repo):
    svc = AuthService(account_repository=mock_repo)
    payload = {"sub": "1", "exp": datetime.utcnow() - timedelta(minutes=1)}
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    with pytest.raises(jwt.ExpiredSignatureError):
        svc.verify_token(token)
