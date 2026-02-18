import pytest
from repositories.users import UserRepository
from repositories.ads import AdRepository


@pytest.mark.asyncio
async def test_create_user(user_repository: UserRepository):
    """Проверяет создание пользователя"""
    user = await user_repository.create(
        name="John Doe",
        email=f"john_{id(user_repository)}@example.com",
        is_verified=True
    )
    
    assert user.id > 0
    assert user.name == "John Doe"
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_create_ad(ad_repository: AdRepository, test_user):
    """Проверяет создание объявления"""
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


@pytest.mark.asyncio
async def test_get_ad_with_user(ad_repository: AdRepository, verified_user):
    """Проверяет получение объявления с данными пользователя"""
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


@pytest.mark.asyncio
async def test_get_nonexistent_ad(ad_repository: AdRepository):
    """Проверяет получение несуществующего объявления"""
    ad = await ad_repository.get_by_id(99999)
    assert ad is None
