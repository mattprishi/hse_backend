from http import HTTPStatus
from typing import Any, Mapping
from unittest.mock import patch
import pytest


def _base_payload() -> Mapping[str, Any]:
    return dict(
        seller_id=1,
        is_verified_seller=False,
        item_id=10,
        name='Item',
        description='Description text',
        category=5,
        images_qty=2,
    )


@pytest.mark.parametrize("is_verified,images,desc_len", [
    (False, 0, 5),
    (False, 1, 10),
    (True, 0, 5),
])
def test_predict_success(app_client, is_verified, images, desc_len):
    """Тест успешного предсказания с разными параметрами"""
    payload = _base_payload()
    payload['is_verified_seller'] = is_verified
    payload['images_qty'] = images
    payload['description'] = 'x' * desc_len
    
    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.OK
    
    result = response.json()
    assert 'is_violation' in result
    assert 'probability' in result
    assert isinstance(result['is_violation'], bool)
    assert isinstance(result['probability'], float)
    assert 0.0 <= result['probability'] <= 1.0


@pytest.mark.parametrize("field,value", [
    ('name', ''),
    ('description', ''),
    ('seller_id', -1),
    ('item_id', -1),
    ('category', -1),
    ('category', 101),
    ('images_qty', -1),
    ('images_qty', 11),
])
def test_predict_validation_constraint(app_client, field, value):
    """Тест валидации - проверка ограничений полей"""
    payload = _base_payload()
    payload[field] = value
    
    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("field", ['seller_id', 'item_id', 'name', 'description', 'category', 'images_qty'])
def test_predict_validation_missing_field(app_client, field):
    """Тест валидации - отсутствует обязательное поле"""
    payload = _base_payload()
    payload.pop(field)
    
    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("field,value", [
    ('images_qty', 'five'),
    ('category', 'invalid'),
    ('seller_id', 'abc'),
])
def test_predict_validation_type_error(app_client, field, value):
    """Тест валидации - неверный тип данных"""
    payload = _base_payload()
    payload[field] = value
    
    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@patch('routers.predict.prediction_service')
def test_predict_model_not_loaded(mock_service, app_client):
    """Тест обработки ошибки - модель не загружена"""
    mock_service.model = None
    
    payload = _base_payload()
    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
