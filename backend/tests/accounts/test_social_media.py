from tests.base import config
from http import HTTPStatus
from unittest.mock import MagicMock, patch
from utils.social_media_handler import DuplicationError
from accounts.models import User

BASE_URL = f'{config["api"]}/social-medias'


@patch('accounts.apis.SocialMediaFactory')
def test_auth(mock_smf, db, client):
    mock_smf.get_instance.return_value.authenticate.return_value = 'https://abc.dbook.com'

    # with valid type
    resp = client.post(f'{BASE_URL}/auth', data={
        'type': 'twitter',
        'address': config['wallet_addr']
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.OK
    assert resp.data['auth_url'] == 'https://abc.dbook.com'
    assert User.objects.filter(account_addr=config['wallet_addr']).count() == 1

    mock_smf.get_instance.return_value = None

    # with invalid type
    resp = client.post(f'{BASE_URL}/auth', data={
        'type': 'abc',
        'address': config['wallet_addr']
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.OK
    assert resp.data['auth_url'] == ''

    # type not given
    resp = client.post(f'{BASE_URL}/auth', content_type='application/json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST


@patch('accounts.apis.SocialMediaFactory')
@patch('accounts.apis.PlatformContractHandler')
def test_share(mock_pch, mock_smf, db, client):
    mock_pch.return_value.add_author.return_value = True
    resp = client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    mock_pch.return_value.add_author.return_value = False
    resp = client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    mock_smf.get_instance.return_value.link_user_and_share.side_effect = DuplicationError('Duplicated text')
    resp = client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    # [ErrorDetail(string='Duplicated Text', code='invalid')]
    assert resp.data[0].title().lower() == 'duplicated text'

    mock_smf.get_instance.return_value = None
    resp = client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
