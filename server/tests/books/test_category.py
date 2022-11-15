from http import HTTPStatus
from tests.base import config

BASE_URL = f'{config["api"]}/categories'


def test_create(admin_client, client, default_category):
    response = client.post(BASE_URL, data={'name': '111'})
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = admin_client.post(BASE_URL, data={
        'name': 'cat1'
    })
    assert response.status_code == HTTPStatus.CREATED
    assert response.data['name'] == 'cat1'
    assert response.data['level'] == 1
    assert response.data['parent'] is None

    response = admin_client.post(BASE_URL, data={
        'parent': default_category.id,
        'name': 'sub_cat',
        'comment': 'sub_cat'
    })
    assert response.status_code == HTTPStatus.CREATED
    assert response.data['parent'] == default_category.id
    assert response.data['name'] == 'sub_cat'
    assert response.data['level'] == default_category.level + 1
    assert response.data['comment'] == 'sub_cat'


def test_update(admin_client, client, default_category):
    response = client.patch(f'{BASE_URL}/{default_category.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = admin_client.patch(f'{BASE_URL}/{default_category.id}', data={
        'name': 'book',
        'comment': 'book'
    }, content_type='application/json')
    assert response.status_code == HTTPStatus.OK
    assert response.data['name'] == 'book'
    assert response.data['comment'] == 'book'
    assert response.data['level'] == 1
    assert response.data['parent'] is None


def test_get(client, default_category):
    response = client.get(f'{BASE_URL}?name=novel')
    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == 1
    assert response.data[0]['name'] == default_category.name
    assert response.data[0]['parent'] == default_category.parent
    assert response.data[0]['level'] == default_category.level
    assert response.data[0]['comment'] == default_category.comment

    response = client.get(f'{BASE_URL}/{default_category.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.data['name'] == default_category.name
    assert response.data['parent'] == default_category.parent
    assert response.data['level'] == default_category.level
    assert response.data['comment'] == default_category.comment


def test_delete(admin_client, client, default_category):
    response = client.delete(f'{BASE_URL}/{default_category.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = admin_client.delete(f'{BASE_URL}/{default_category.id}')
    assert response.status_code == HTTPStatus.NO_CONTENT
    response = client.get(f'{BASE_URL}/{default_category.id}')
    assert response.status_code == HTTPStatus.NOT_FOUND
