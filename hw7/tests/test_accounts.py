import pytest
from repositories.accounts import AccountRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_create_get_block(account_repository: AccountRepository, setup_database):
    acc = await account_repository.create("user1", "pass1")
    assert acc.id > 0
    assert acc.login == "user1"
    assert not acc.is_blocked
    got = await account_repository.get_by_id(acc.id)
    assert got and got.login == "user1"
    await account_repository.block(acc.id)
    got = await account_repository.get_by_id(acc.id)
    assert got and got.is_blocked is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_by_login_and_password(account_repository: AccountRepository, setup_database):
    await account_repository.create("alice", "secret")
    found = await account_repository.get_by_login_and_password("alice", "secret")
    assert found and found.login == "alice"
    assert await account_repository.get_by_login_and_password("alice", "wrong") is None
    assert await account_repository.get_by_login_and_password("bob", "secret") is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_delete(account_repository: AccountRepository, setup_database):
    acc = await account_repository.create("deluser", "p")
    await account_repository.delete(acc.id)
    assert await account_repository.get_by_id(acc.id) is None
