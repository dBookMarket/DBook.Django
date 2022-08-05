from utils.social_media_handler import TwitterHandler, DuplicationError, RequestError
from unittest.mock import patch, Mock
from accounts.models import User, SocialMedia
from utils.enums import SocialMediaType
import pytest
# from tweepy.errors import Forbidden
# from requests.exceptions import JSONDecodeError


class Forbidden(Exception):
    pass

@patch('utils.social_media_handler.requests')
def test_get_access_token(mock_reqs):
    th = TwitterHandler()

    token='abc'
    verifier='bcd'

    # not ok
    mock_reqs.post.return_value.status_code = 400
    with pytest.raises(RequestError):
        th.get_access_token(token, verifier)

    # good response
    mock_reqs.post.return_value.status_code = 200
    mock_reqs.post.return_value.json.return_value = {'oauth_token': 'xxx', 'oauth_token_secret': 'xxx'}
    access_token, access_token_secret = th.get_access_token(token, verifier)
    assert access_token == 'xxx'
    assert access_token_secret == 'xxx'

    # json exception
    # todo TypeError: catching classes that do not inherit from BaseException is not allowed
    # mock_reqs.post.return_value.json.side_effect = JSONDecodeError('invalid text', 'doc', 0)
    # mock_reqs.post.return_value.text = 'oauth_token=ttt&oauth_token_secret=ddd'
    # access_token, access_token_secret = th.get_access_token(token, verifier)
    # assert access_token == 'ttt'
    # assert access_token_secret == 'ddd'


@patch('utils.social_media_handler.tweepy')
def test_get_user(mock_tweepy):
    mock_tweepy.Client.return_value.get_me.return_value.data = {
        'id': '123123',
        'username': 'test'
    }
    th = TwitterHandler()

    access_token = 'abc'
    access_token_secret = 'bcd'

    mock_tweepy.Client.return_value.get_me.return_value.status_code = 200
    res = th.get_user(access_token, access_token_secret)
    assert res['account_id'] == '123123'
    assert res['username'] == 'test'

    mock_tweepy.Client.return_value.get_me.return_value.status_code = 400
    with pytest.raises(RequestError):
        th.get_user(access_token, access_token_secret)

    # exception
    mock_tweepy.Client.return_value.get_me.side_effect = Exception()
    with pytest.raises(RequestError):
        th.get_user(access_token, access_token_secret)


@patch('utils.social_media_handler.tweepy')
def test_share(mock_tweepy):
    th = TwitterHandler()

    access_token = 'abc'
    access_token_secret = 'bcd'

    mock_tweepy.Client.return_value.create_tweet.return_value.status_code = 200
    mock_tweepy.Client.return_value.create_tweet.return_value.data = {'text': 'abc'}
    res = th.share(access_token, access_token_secret)
    assert res == {'text': 'abc'}

    # bad request
    mock_tweepy.Client.return_value.create_tweet.return_value.status_code = 400
    with pytest.raises(RequestError):
        th.share(access_token, access_token_secret)

    # duplication
    # todo TypeError: catching classes that do not inherit from BaseException is not allowed
    # mock_tweepy.Client.return_value.create_tweet.side_effect = Forbidden()
    # with pytest.raises(DuplicationError):
    #     th.share(access_token, access_token_secret)

    # other exception
    # mock_tweepy.Client.return_value.create_tweet.side_effect = Exception()
    # with pytest.raises(RequestError):
    #     th.share(access_token, access_token_secret)


@patch('utils.social_media_handler.tweepy')
def test_authenticate(mock_tweepy):
    mock_tweepy.OAuth1UserHandler.return_value.get_authorization_url.return_value = 'abc.com'
    th = TwitterHandler()

    res = th.authenticate()
    assert res == 'abc.com'

    mock_tweepy.OAuth1UserHandler.return_value.get_authorization_url.side_effect = Exception()
    with pytest.raises(RequestError):
        th.authenticate()


def test_link_user_and_share(db):
    wallet_addr = "0x123abc"
    token = 'abc'
    verifier = 'bcd'

    th = TwitterHandler()

    th.get_access_token = Mock()
    th.get_user = Mock()
    th.share = Mock()

    th.get_access_token.return_value = ('xxx', 'yyy')
    th.get_user.return_value = {'account_id': '123123', 'username': 'test'}

    # create an user with wallet_addr
    user = User.objects.create_user(username='1q2w3e', account_addr=wallet_addr)

    th.link_user_and_share(wallet_addr, token, verifier)

    social_media = SocialMedia.objects.get(user=user, type=SocialMediaType.TWITTER.value)
    assert social_media.account_id == '123123'
    assert social_media.username == 'test'
    assert social_media.shared

