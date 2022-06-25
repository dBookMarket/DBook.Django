from tests.base import config
from http import HTTPStatus
from tests import helper
import stores.models

BASE_URL = f'{config["api"]}/transactions'


def test_transaction(auth_client, default_user,
                     auth_client_with_normal_user,
                     client, default_category):
    obj = helper.trade_book(auth_client, default_category)
    obj_trade = stores.models.Trade.objects.get(issue=obj, user=default_user)
    response = client.post(BASE_URL)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    # buy a book
    response = auth_client_with_normal_user.post(f'{config["api"]}/transactions', data={
        'issue': obj.id,
        'trade': obj_trade.id,
        'amount': 1,
        'price': obj_trade.price,
        'status': 'success',
        'hash': 'abcdefg1234'
    })
    transaction_id = response.data['id']
    assert response.status_code == HTTPStatus.CREATED
    assert response.data['issue']['id'] == obj.id
    assert response.data['trade'] == obj_trade.id
    assert response.data['amount'] == 1
    assert response.data['status'] == 'success'
    assert response.data['hash'] == 'abcdefg1234'

    # get many transactions
    response = client.get(f'{BASE_URL}?issue={obj.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['issue']['id'] == obj.id
    assert response.data['results'][0]['trade'] == obj_trade.id
    assert response.data['results'][0]['amount'] == 1
    assert response.data['results'][0]['status'] == 'success'
    assert response.data['results'][0]['hash'] == 'abcdefg1234'
    # get one transaction
    response = client.get(f'{BASE_URL}/{transaction_id}')
    assert response.status_code == HTTPStatus.OK
    assert response.data['issue']['id'] == obj.id
    assert response.data['trade'] == obj_trade.id
    assert response.data['amount'] == 1
    assert response.data['status'] == 'success'
    assert response.data['hash'] == 'abcdefg1234'

    # get my transactions
    response = auth_client_with_normal_user.get(f'{BASE_URL}/current-user')
    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] == 1
    assert response.data['results'][0]['issue']['id'] == obj.id
    assert response.data['results'][0]['trade'] == obj_trade.id
    assert response.data['results'][0]['amount'] == 1
    assert response.data['results'][0]['status'] == 'success'
    assert response.data['results'][0]['hash'] == 'abcdefg1234'
