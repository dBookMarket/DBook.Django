from tests.base import config
from http import HTTPStatus
from unittest.mock import MagicMock, patch
from utils.social_media_handler import DuplicationError
from accounts.models import User

BASE_URL = f'{config["api"]}/social-medias'


@patch('accounts.apis.Cache')
@patch('accounts.apis.pickle')
@patch('accounts.apis.SocialMediaFactory')
def test_auth(mock_smf, mock_pickle, mock_cache, db, client):
    mock_smf.get_instance.return_value.authenticate.return_value = 'https://abc.dbook.com'
    mock_pickle.dumps.return_value = b'abc'

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


@patch('accounts.apis.pickle')
@patch('accounts.apis.Cache')
@patch('accounts.apis.PlatformContractHandler')
def test_create_msg(mock_pch, mock_cache, mock_pickle, db, client):
    mock_pch.return_value.add_author.return_value = True
    mock_cache.return_value.get.return_value = None
    resp = client.post(f'{BASE_URL}/post', data={
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    mock_pch.return_value.add_author.return_value = False
    resp = client.post(f'{BASE_URL}/post', data={
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST

    mock_cache.return_value.get.return_value = 'abc'
    mock_pickle.loads.return_value = None
    resp = client.post(f'{BASE_URL}/post', data={
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.OK
    assert resp.data['status'] == 'failure'

    mock_pickle.loads.return_value = MagicMock()
    mock_pickle.loads.return_value.create_msg.return_value = {'text': 'test'}
    mock_pch.return_value.add_author.return_value = True
    resp = client.post(f'{BASE_URL}/post', data={
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.OK
    assert resp.data['status'] == 'success'

    mock_pickle.loads.return_value.create_msg.side_effect = DuplicationError('Duplicated text')
    resp = client.post(f'{BASE_URL}/post', data={
        'address': config['wallet_addr'],
        'oauth_verifier': 'abcdefghi'
    }, content_type='application/json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    # [ErrorDetail(string='Duplicated Text', code='invalid')]
    assert resp.data[0].title().lower() == 'duplicated text'



# def test_verify_msg(db, client):
#     SocialMediaFactory.get_instance = MagicMock()
#     SocialMediaFactory.get_instance.return_value.verify_msg.return_value = True
#     PlatformContractHandler.add_author = MagicMock()
#     PlatformContractHandler.add_author.return_value = True
#
#     resp = client.post(f'{BASE_URL}/verify', data={
#         'address': config['wallet_addr'],
#         'type': 'twitter'
#     }, content_type='application/json')
#     assert resp.status_code == HTTPStatus.OK
#     assert resp.data['status'] == 'success'
#
#     # type not given
#     resp = client.post(f'{BASE_URL}/verify', data={
#         'address': config['wallet_addr'],
#         'type': ''
#     }, content_type='application/json')
#     assert resp.status_code == HTTPStatus.BAD_REQUEST
#     assert 'type' in resp.data
#
#     # add perm failed
#     PlatformContractHandler.add_author.return_value = False
#     resp = client.post(f'{BASE_URL}/verify', data={
#         'address': config['wallet_addr'],
#         'type': 'twitter'
#     }, content_type='application/json')
#     assert resp.status_code == HTTPStatus.BAD_REQUEST
#
#     # invalid type
#     SocialMediaFactory.get_instance.return_value = None
#     resp = client.post(f'{BASE_URL}/verify', data={
#         'address': config['wallet_addr'],
#         'type': 'abc'
#     }, content_type='application/json')
#     assert resp.status_code == HTTPStatus.OK
#     assert resp.data['status'] == 'failure'

