import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success(app_client: AsyncClient, test_account):
    r = await app_client.post("/login", json={"login": test_account["login"], "password": test_account["password"]})
    assert r.status_code == 200
    set_cookie = r.headers.get("set-cookie") or r.headers.get("Set-Cookie") or ""
    assert "access_token=" in set_cookie


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_credentials(app_client: AsyncClient, test_account):
    r = await app_client.post("/login", json={"login": test_account["login"], "password": "wrong"})
    assert r.status_code == 401
    r2 = await app_client.post("/login", json={"login": "nonexistent", "password": "x"})
    assert r2.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_blocked_user(app_client: AsyncClient, account_repository, setup_database):
    import os
    login = f"blocked_{os.urandom(4).hex()}"
    acc = await account_repository.create(login, "pass")
    await account_repository.block(acc.id)
    r = await app_client.post("/login", json={"login": login, "password": "pass"})
    assert r.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_validation_empty_fields(app_client: AsyncClient):
    r = await app_client.post("/login", json={"login": "", "password": "x"})
    assert r.status_code == 422
    r2 = await app_client.post("/login", json={"login": "user", "password": ""})
    assert r2.status_code == 422
