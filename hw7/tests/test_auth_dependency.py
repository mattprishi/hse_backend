import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from dependencies import get_current_user
from models.entities import Account


@pytest.mark.asyncio
async def test_get_current_user_no_token():
    auth = MagicMock()
    with pytest.raises(HTTPException) as exc:
        await get_current_user(access_token=None, auth_service=auth)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    auth = MagicMock()
    auth.verify_token.side_effect = Exception("bad")
    with pytest.raises(HTTPException) as exc:
        await get_current_user(access_token="bad", auth_service=auth)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_blocked():
    auth = MagicMock()
    auth.verify_token.return_value = 1
    auth.account_repository.get_by_id = AsyncMock(return_value=Account(id=1, login="x", password="", is_blocked=True))
    with pytest.raises(HTTPException) as exc:
        await get_current_user(access_token="t", auth_service=auth)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_success():
    auth = MagicMock()
    auth.verify_token.return_value = 1
    acc = Account(id=1, login="u", password="", is_blocked=False)
    auth.account_repository.get_by_id = AsyncMock(return_value=acc)
    result = await get_current_user(access_token="t", auth_service=auth)
    assert result == acc
