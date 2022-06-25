from tests.base import config
from http import HTTPStatus
from tests import helper

BASE_URL = f'{config["api"]}/assets'


def test_get(auth_client, client, default_category):
    response = client.get(BASE_URL)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = auth_client.get(BASE_URL)
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 0

    # trade an issue
    issue = helper.trade_book(auth_client, default_category)
    response = auth_client.get(BASE_URL)
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['amount'] == issue.amount
    asset_id = response.data['results'][0]['id']
    # read one
    response = client.get(f'{BASE_URL}/{asset_id}/read')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    response = auth_client.get(f'{BASE_URL}/{asset_id}/read')
    assert response.status_code == HTTPStatus.OK
    assert response.data['files'] == []
    assert response.data['sk'] == ''
