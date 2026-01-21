from http import HTTPStatus
from typing import Any, Mapping


def _base_payload() -> Mapping[str, Any]:
    return dict(
        seller_id=1,
        is_verified_seller=False,
        item_id=10,
        name='Item',
        description='Desc',
        category=1,
        images_qty=0,
    )


def test_predict_verified_seller(app_client):
    payload = _base_payload()
    payload['is_verified_seller'] = True
    payload['images_qty'] = 0

    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.OK
    assert response.json() is True


def test_predict_with_images(app_client):
    payload = _base_payload()
    payload['images_qty'] = 2

    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.OK
    assert response.json() is True


def test_predict_without_images(app_client):
    payload = _base_payload()
    payload['images_qty'] = 0

    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.OK
    assert response.json() is False


def test_predict_validation_missing_field(app_client):
    payload = _base_payload()
    payload.pop('item_id')

    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_predict_validation_type_error(app_client):
    payload = _base_payload()
    payload['images_qty'] = 'five'

    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_predict_business_error(app_client):
    payload = _base_payload()
    payload['category'] = -1

    response = app_client.post('/predict', json=payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST


