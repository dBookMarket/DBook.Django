from tests.base import config
from http import HTTPStatus
from tests import helper
import stores.models

BASE_URL = f'{config["api"]}/trades'


def test_get(auth_client, client, default_user, default_category):
    obj = helper.trade_book(auth_client, default_category)
    obj_trade = stores.models.Trade.objects.get(issue=obj, user=default_user)
    response = client.get(f'{BASE_URL}?issue={obj.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['issue'] == obj.id
    assert response.data['results'][0]['amount'] == obj.amount
    assert response.data['results'][0]['price'] == obj.price
    assert response.data['results'][0]['first_release']

    response = client.get(f'{BASE_URL}/{obj_trade.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.data['issue'] == obj.id
    assert response.data['amount'] == obj.amount
    assert response.data['price'] == obj.price
    assert response.data['first_release']

    response = auth_client.get(f'{BASE_URL}/current-user')
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['issue'] == obj.id
    assert response.data['results'][0]['amount'] == obj.amount
    assert response.data['results'][0]['price'] == obj.price
    assert response.data['results'][0]['first_release']


def test_create(auth_client, default_user, auth_client_with_normal_user, client, default_category):
    obj = helper.trade_book(auth_client, default_category)
    response = client.post(BASE_URL)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    obj_trade = stores.models.Trade.objects.get(issue=obj, user=default_user)
    # buy a book
    auth_client_with_normal_user.post(f'{config["api"]}/transactions', data={
        'issue': obj.id,
        'trade': obj_trade.id,
        'amount': 1,
        'price': obj_trade.price,
        'status': 'success',
        'hash': 'abcdefg1234'
    })
    # trade book
    response = auth_client_with_normal_user.post(BASE_URL, data={
        'issue': obj.id,
        'amount': 3,
        'price': 20
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'amount' in response.data

    response = auth_client_with_normal_user.post(BASE_URL, data={
        'issue': obj.id,
        'amount': 1,
        'price': 20
    })
    assert response.status_code == HTTPStatus.CREATED
    assert response.data['issue'] == obj.id
    assert response.data['amount'] == 1
    assert response.data['price'] == 20


def test_update(auth_client, default_user, default_category):
    obj = helper.trade_book(auth_client, default_category)
    obj_trade = stores.models.Trade.objects.get(issue=obj, user=default_user)

    response = auth_client.patch(f'{BASE_URL}/{obj_trade.id}', data={
        'amount': 5,
        'price': 30
    })

    assert response.status_code == HTTPStatus.OK
    assert response.data['amount'] == 5
    assert response.data['price'] == 30


def test_delete(auth_client, auth_client_with_normal_user, default_user, default_category):
    obj = helper.trade_book(auth_client, default_category)
    obj_trade = stores.models.Trade.objects.get(issue=obj, user=default_user)

    # first release cannot be removed
    response = auth_client.delete(f'{BASE_URL}/{obj_trade.id}')
    assert response.status_code == HTTPStatus.BAD_REQUEST

    # buy a book
    auth_client_with_normal_user.post(f'{config["api"]}/transactions', data={
        'issue': obj.id,
        'trade': obj_trade.id,
        'amount': 1,
        'price': obj_trade.price,
        'status': 'success',
        'hash': 'abcdefg1234'
    })
    response = auth_client_with_normal_user.post(BASE_URL, data={
        'issue': obj.id,
        'amount': 1,
        'price': 20
    })
    trade_id = response.data['id']
    response = auth_client_with_normal_user.delete(f'{BASE_URL}/{trade_id}')
    assert response.status_code == HTTPStatus.NO_CONTENT

    response = auth_client_with_normal_user.get(f'{BASE_URL}/{trade_id}')
    assert response.status_code == HTTPStatus.NOT_FOUND
