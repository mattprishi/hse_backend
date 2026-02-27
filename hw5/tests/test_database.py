import pytest
from repositories.users import UserRepository
from repositories.ads import AdRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_user(user_repository: UserRepository):
    """Интеграционный тест: проверяет создание пользователя в БД"""
    user = await user_repository.create(
        name="John Doe",
        email=f"john_{id(user_repository)}@example.com",
        is_verified=True
    )
    
    assert user.id > 0
    assert user.name == "John Doe"
    assert user.is_verified is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_ad(ad_repository: AdRepository, test_user):
    """Интеграционный тест: проверяет создание объявления в БД"""
    ad = await ad_repository.create(
        user_id=test_user.id,
        title="Test Ad",
        description="Test Description",
        category=25,
        images_qty=5,
        price=1500.0
    )
    
    assert ad.id > 0
    assert ad.user_id == test_user.id
    assert ad.title == "Test Ad"
    assert ad.category == 25
    assert ad.images_qty == 5
    assert ad.price == 1500.0
    assert ad.is_closed is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_ad_with_user(ad_repository: AdRepository, verified_user):
    """Интеграционный тест: проверяет получение объявления с данными пользователя из БД"""
    ad = await ad_repository.create(
        user_id=verified_user.id,
        title="Ad with User",
        description="Description",
        category=50,
        images_qty=3,
        price=2000.0
    )
    
    ad_data = await ad_repository.get_with_user(ad.id)
    
    assert ad_data is not None
    assert ad_data['id'] == ad.id
    assert ad_data['user_id'] == verified_user.id
    assert ad_data['is_verified_seller'] is True
    assert ad_data['title'] == "Ad with User"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_nonexistent_ad(ad_repository: AdRepository):
    """Интеграционный тест: проверяет получение несуществующего объявления"""
    ad = await ad_repository.get_by_id(99999)
    assert ad is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_close_ad(ad_repository: AdRepository, test_user):
    """Интеграционный тест: проверяет закрытие объявления в БД"""
    ad = await ad_repository.create(
        user_id=test_user.id,
        title="Ad to Close",
        description="Will be closed",
        category=30,
        images_qty=2,
        price=1000.0
    )
    
    closed = await ad_repository.close(ad.id)
    assert closed is True
    
    ad_data = await ad_repository.get_with_user(ad.id)
    assert ad_data is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_close_nonexistent_ad(ad_repository: AdRepository):
    """Интеграционный тест: проверяет закрытие несуществующего объявления"""
    closed = await ad_repository.close(99999)
    assert closed is False
