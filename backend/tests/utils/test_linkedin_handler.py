from utils.social_media_handler import LinkedInHandler, RequestError
from unittest.mock import patch, Mock
from accounts.models import User, SocialMedia
from utils.enums import SocialMediaType
import pytest


@patch('utils.social_media_handler.requests')
def test_get_access_token(mock_reqs):
    token = 'abc'
    verifier = 'bcd'

    lh = LinkedInHandler()

    # verify failed
    with pytest.raises(RequestError):
        lh.get_access_token(token, verifier)

    verifier = LinkedInHandler.STATE

    # not ok
    mock_reqs.post.return_value.ok = False
    with pytest.raises(RequestError):
        lh.get_access_token(token, verifier)

    # good request
    mock_reqs.post.return_value.ok = True
    mock_reqs.post.return_value.json.return_value = {'access_token': 'xxx'}
    access_token = lh.get_access_token(token, verifier)
    assert access_token == 'xxx'


@patch('utils.social_media_handler.requests')
def test_get_user(mock_reqs):
    access_token = 'xxx'
    lh = LinkedInHandler()

    # not ok
    mock_reqs.get.return_value.ok = False
    with pytest.raises(RequestError):
        lh.get_user(access_token)

    # good request
    mock_reqs.get.return_value.ok = True
    mock_reqs.get.return_value.json.return_value = {'id': '123123'}
    res = lh.get_user(access_token)
    assert res['account_id'] == '123123'


@patch('utils.social_media_handler.requests')
def test_share(mock_reqs):
    access_token = 'xxx'
    owner = 'urn:li:person:123123'
    content = 'xxx'
    lh = LinkedInHandler()

    # not ok
    mock_reqs.post.return_value.ok = False
    with pytest.raises(RequestError):
        lh.share(access_token, owner, content)

    # good request
    mock_reqs.post.return_value.ok = True
    mock_reqs.post.return_value.json.return_value = {'text': 'shared'}
    res = lh.share(access_token, owner, content)
    assert res == {'text': 'shared'}


def test_authenticate():
    lh = LinkedInHandler()
    auth_uri = lh.authenticate()
    assert auth_uri


def test_link_user_and_share(db):
    wallet_addr = '0x123xyz'
    token = 'abc'
    verifier = LinkedInHandler.STATE
    content = 'xxx'

    lh = LinkedInHandler()

    lh.get_access_token = Mock()
    lh.get_user = Mock()
    lh.share = Mock()

    lh.get_access_token.return_value = 'xxx'
    lh.get_user.return_value = {'account_id': '123123'}

    # create an user
    user = User.objects.create_user(username='xyz', account_addr=wallet_addr)

    lh.link_user_and_share(wallet_addr, token, verifier, content)

    social_media = SocialMedia.objects.get(user=user, type=SocialMediaType.LINKEDIN.value)
    assert social_media.account_id == '123123'
    assert social_media.username == ''
    assert social_media.shared