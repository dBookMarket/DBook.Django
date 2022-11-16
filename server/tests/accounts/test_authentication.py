from http import HTTPStatus
from tests.base import config
from web3.auto import w3
from eth_account.messages import encode_defunct
from rest_framework.test import APIClient
import pytest

wallet_addr = '0xa59B8B0f5859A9aCBa70fb5b5697581c81A86f84'
private_key = '43c0f49674816785bb4499ac016034f7ac6007967f9e629d66caf750185f2d85'


@pytest.mark.django_db
def test_nonce(client):
    addr = 'abcd'
    response = client.post(f'{config["api"]}/nonce', data={
        'address': addr
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'address' in response.data

    response = client.post(f'{config["api"]}/nonce', data={
        'address': wallet_addr
    })
    assert response.status_code == HTTPStatus.CREATED
    assert 'nonce' in response.data
    last_nonce = response.data['nonce']
    # nonce is difference for each request
    response = client.post(f'{config["api"]}/nonce', data={
        'address': wallet_addr
    })
    assert response.status_code == HTTPStatus.CREATED
    assert response.data['nonce'] != last_nonce


@pytest.mark.django_db
def test_login(client):
    # get nonce
    response = client.post(f'{config["api"]}/nonce', data={
        'address': wallet_addr
    })
    nonce = response.data['nonce']
    # login
    # 1, sign nonce
    msg = encode_defunct(text=nonce)
    signed_msg = w3.eth.account.sign_message(msg, private_key=private_key)
    signature = signed_msg.signature.hex()
    response = client.post(f'{config["api"]}/login', data={
        'address': wallet_addr,
        'signature': signature
    })
    assert response.status_code == HTTPStatus.CREATED
    assert 'token' in response.data
    # invalid login
    addr = 'abcdefg123'
    response = client.post(f'{config["api"]}/login', data={
        'address': addr,
        'signature': signature
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST
    response = client.post(f'{config["api"]}/login', data={
        'address': wallet_addr,
        'signature': 'sdfsdfdssfdsdfsdf'
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_logout(client):
    # get nonce
    response = client.post(f'{config["api"]}/nonce', data={
        'address': wallet_addr
    })
    nonce = response.data['nonce']
    # login
    # 1, sign nonce
    msg = encode_defunct(text=nonce)
    signed_msg = w3.eth.account.sign_message(msg, private_key=private_key)
    signature = signed_msg.signature.hex()

    response = client.post(f'{config["api"]}/login', data={
        'address': wallet_addr,
        'signature': signature
    })
    token = response.data['token']
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = api_client.post(f'{config["api"]}/logout')
    assert response.status_code == HTTPStatus.CREATED
