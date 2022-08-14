from tests.base import config
from http import HTTPStatus
from unittest.mock import MagicMock, patch
from utils.social_media_handler import DuplicationError
from utils.enums import SocialMediaType, UserType
from accounts.models import User, SocialMedia

BASE_URL = f'{config["api"]}/social-medias'


@patch('accounts.apis.SocialMediaFactory')
def test_auth(mock_smf, db, client, auth_client):
    mock_smf.get_instance.return_value.authenticate.return_value = 'https://abc.dbook.com'

    # no auth
    resp = client.post(f'{BASE_URL}/auth', data={
        'type': 'twitter',
    }, format='json')
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

    # with valid type
    resp = auth_client.post(f'{BASE_URL}/auth', data={
        'type': 'twitter',
    }, format='json')
    assert resp.status_code == HTTPStatus.CREATED
    assert resp.data['auth_uri'] == 'https://abc.dbook.com'

    mock_smf.get_instance.return_value = None

    # with invalid type
    resp = auth_client.post(f'{BASE_URL}/auth', data={
        'type': 'abc'
    }, format='json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert 'type' in resp.data

    # type not given
    resp = auth_client.post(f'{BASE_URL}/auth', format='json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert 'type' in resp.data


@patch('accounts.apis.SocialMediaFactory')
@patch('accounts.apis.PlatformContractHandler')
def test_share(mock_pch, mock_smf, db, client, auth_client, default_user):
    # not auth
    resp = client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

    # auth twitter firstly
    resp = auth_client.post(f'{BASE_URL}/share', data={
        'type': 'linkedin',
        'content': 'xxxxx',
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert 'detail' in resp.data

    # type is required
    resp = auth_client.post(f'{BASE_URL}/share', data={
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert 'type' in resp.data

    # content is required
    resp = auth_client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert 'content' in resp.data

    # success for twitter
    resp = auth_client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'content': 'aaaaaa',
        'oauth_token': 'xxxxx',
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.CREATED

    # verify linkedin
    SocialMedia.objects.create(user=default_user, type=SocialMediaType.TWITTER.value, shared=True,
                               account_id='123', username='abc')

    # add perm from contract failed
    mock_pch.return_value.add_author.return_value = False
    resp = auth_client.post(f'{BASE_URL}/share', data={
        'type': 'linkedin',
        'content': 'aaaaaa',
        'oauth_token': 'xxxxx',
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert 'detail' in resp.data

    # success for linkedin
    mock_pch.return_value.add_author.return_value = True
    resp = auth_client.post(f'{BASE_URL}/share', data={
        'type': 'linkedin',
        'content': 'aaaaaa',
        'oauth_token': 'xxxxx',
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.CREATED
    _user = User.objects.get(id=default_user.id)
    assert _user.type == UserType.AUTHOR.value

    # duplicated text
    mock_smf.get_instance.return_value.link_user_and_share.side_effect = DuplicationError('Duplicated text')
    resp = auth_client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'content': 'aaaaaa',
        'oauth_token': 'xxxxx',
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.data['detail'] == 'Duplicated text'

    # unknown error
    mock_smf.get_instance.return_value = None
    resp = auth_client.post(f'{BASE_URL}/share', data={
        'type': 'twitter',
        'content': 'aaaaaa',
        'oauth_token': 'xxxxx',
        'oauth_verifier': 'abcdefghi'
    }, format='json')
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_check_status(client, auth_client, default_user):
    resp = client.get(f'{BASE_URL}/verification-state')
    assert resp.status_code == HTTPStatus.OK
    assert not resp.data['twitter']
    assert not resp.data['linkedin']

    resp = auth_client.get(f'{BASE_URL}/verification-state')
    assert resp.status_code == HTTPStatus.OK
    assert not resp.data['twitter']
    assert not resp.data['linkedin']

    # add twitter
    SocialMedia.objects.create(user=default_user, type=SocialMediaType.TWITTER.value, shared=True,
                               account_id='abc', username='123')
    resp = auth_client.get(f'{BASE_URL}/verification-state')
    assert resp.status_code == HTTPStatus.OK
    assert resp.data['twitter']
    assert not resp.data['linkedin']

    # add linkedin
    SocialMedia.objects.create(user=default_user, type=SocialMediaType.LINKEDIN.value, shared=True,
                               account_id='abc', username='123')
    resp = auth_client.get(f'{BASE_URL}/verification-state')
    assert resp.status_code == HTTPStatus.OK
    assert resp.data['twitter']
    assert resp.data['linkedin']
