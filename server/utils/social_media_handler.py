import tweepy
from users.models import User, Account
from utils.enums import SocialMediaType
import requests
import json
from urllib.parse import quote

from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SocialMediaFactory(object):

    def __new__(cls, _type: str, *args, **kwargs):
        if _type == 'twitter':
            return TwitterHandler()
        if _type == 'linkedin':
            return LinkedInHandler()
        return None

    # @classmethod
    # def get_instance(cls, _type: str):
    #     if _type == 'twitter':
    #         return TwitterHandler()
    #     if _type == 'linkedin':
    #         return LinkedInHandler()
    #     return None


class DuplicationError(Exception):
    pass


class RequestError(Exception):
    pass


class SocialMediaHandler(object):
    """
    Social Media Account base handler class.
    """
    REDIRECT_URI = settings.SOCIAL_MEDIA_REDIRECT_URI

    def txt_to_json(self, text: str) -> dict:
        """
        Convert response text to json format.
        """
        data = dict()
        for v in text.split('&'):
            l_v = v.split('=')
            if len(l_v) != 2:
                raise ValueError('The text is invalid, which is not the format of response text.')
            data[l_v[0]] = l_v[1]
        return data

    def share(self, **kwargs):
        pass

    def authenticate(self):
        pass

    def link_user_and_share(self, **kwargs):
        pass


class TwitterHandler(SocialMediaHandler):
    """
    This class is for calling the twitter's api to read and write the tweets. The version of twitter api is v2.
    """
    REDIRECT_URI = f'{settings.SOCIAL_MEDIA_REDIRECT_URI}?type=twitter&isAuth=true'
    CONFIG = settings.TWITTER_SETTINGS

    def _get_oauth_uri(self, endpoint):
        return f'https://api.twitter.com/oauth/{endpoint}'

    def get_access_token(self, token: str, verifier: str) -> (str, str):
        """
        Get the user's oauth token, which is granted by him/her.

        args:
            token: str, which is from the redirect uri when the user granted.

            verifier: str, which is from the redirect uri when the user granted.

        returns:
            access_token: str,
            access_token_secret: str
        """
        _data = {
            # 'oauth_consumer_key': self.TWITTER_CONF['consumer_key'],
            'oauth_token': token,
            'oauth_verifier': verifier
        }

        _uri = self._get_oauth_uri('access_token')

        resp = requests.post(_uri, data=_data)

        logger.info('response from access token api ->', resp, resp.text, resp.content)

        if not resp.ok:
            raise RequestError(f'Fail to get access token, error is {resp.text}')

        try:
            resp_data = resp.json()
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f'Warning: Exception when calling TwitterHandler.get_access_token -> {e}')
            resp_data = self.txt_to_json(resp.text)

        return resp_data['oauth_token'], resp_data['oauth_token_secret']

    def get_user(self, access_token: str, access_token_secret: str):
        """
        Link the user's twitter account to the dbook platform account, which is to check the user's identity.

        args:
            access_token: str, from get_access_token()

            access_token_secret: str, from get_access_token()
        """
        user_client = tweepy.Client(consumer_key=self.CONFIG['consumer_key'],
                                    consumer_secret=self.CONFIG['consumer_secret'],
                                    access_token=access_token,
                                    access_token_secret=access_token_secret)
        # get user's id to store into db, which links to the user's platform account.
        try:
            resp = user_client.get_me()
        except Exception as e:
            logger.error(f'Exception when calling TwitterHandler.get_user -> {e}')
            raise RequestError('Fail to get user profile, please ask manager for help.')

        if resp.errors:
            raise RequestError(f'Fail to get user profile, errors: {resp.errors}')

        return {
            'account_id': resp.data['id'],
            'username': resp.data['username']
        }

    def share(self, access_token: str, access_token_secret: str, content: str) -> dict:
        """
        post a tweet about d-book to make sure the user is real if an user want to be an author of the d-book platform.

        args:
            access_token: str, from get_access_token()

            access_token_secret: str, from get_access_token()

            content: str, the sharing content

        returns:
            data: dict, the data from response.
        """
        user_client = tweepy.Client(consumer_key=self.CONFIG['consumer_key'],
                                    consumer_secret=self.CONFIG['consumer_secret'],
                                    access_token=access_token,
                                    access_token_secret=access_token_secret)
        # create a tweet
        try:
            resp = user_client.create_tweet(text=content)
        except tweepy.errors.Forbidden as e:
            logger.error(f'Exception when calling TwitterHandler.share -> {e}')
            raise DuplicationError('You already tweet one.')
        except Exception as e:
            logger.error(f'Exception when calling TwitterHandler.share -> {e}')
            raise RequestError('Fail to send share, please try later...')

        if resp.errors:
            raise RequestError(f'Fail to send share, errors: {resp.errors}')

        return resp.data

    def authenticate(self) -> str:
        """
        sign in twitter to get the user's auth token, which needs the grants from the user.
        When the user's grant is given, the dbook platform will post a tweet about dbook with the user's account.

        returns:
            auth_url: str, the authority url from the user.
        """
        oauth_user_handler = tweepy.OAuth1UserHandler(self.CONFIG['consumer_key'],
                                                      self.CONFIG['consumer_secret'],
                                                      callback=self.REDIRECT_URI)
        try:
            auth_url = oauth_user_handler.get_authorization_url(signin_with_twitter=True)
        except Exception as e:
            logger.error(f'Exception when calling TwitterHandler.authenticate -> {e}')
            raise RequestError('Fail to authenticate, please try later...')
        logger.info('auth url->', auth_url)
        return auth_url

    def link_user_and_share(self, wallet_addr: str, token: str, verifier: str, content: str):
        """
        Get user info to save into db and send share with the user's account.

        args:
            wallet_addr: str, the wallet address from metaMask.

            token: str, which is from the redirect uri when the user granted.

            verifier: str, which is from the redirect uri when the user granted.

            content: str, the sharing content from user interface.
        """
        # get access token
        access_token, access_token_secret = self.get_access_token(token, verifier)

        # get user info
        sm_user = self.get_user(access_token, access_token_secret)
        # save user
        user = User.objects.get(address=wallet_addr)
        social_media, _ = Account.objects.update_or_create(user=user, type=SocialMediaType.TWITTER.value,
                                                           defaults={**sm_user, **{'shared': False}})

        # send share
        self.share(access_token, access_token_secret, content)

        # tag user
        social_media.shared = True
        social_media.save()


class LinkedInHandler(SocialMediaHandler):
    REDIRECT_URI = f'{settings.SOCIAL_MEDIA_REDIRECT_URI}?type=linkedin&isAuth=true'
    CONFIG = settings.LINKEDIN_SETTINGS
    STATE = 'rwer243fa2sfse'

    def _get_oauth_uri(self, endpoint):
        return f'https://www.linkedin.com/oauth/v2/{endpoint}'

    def _get_uri(self, endpoint):
        return f'https://api.linkedin.com/v2/{endpoint}'

    def get_access_token(self, token: str, verifier: str) -> str:
        """
        Get the user's access token from LinkedIn.

        args:
            token: str, the OAuth 2.0 authorization code.

            verifier: str, A value used to test for possible CSRF attacks.

        returns:
            access_token: str
        """
        if verifier != self.STATE:
            raise RequestError('The state of request has been changed, please check again.')

        _data = {
            'grant_type': 'authorization_code',
            'code': token,
            'redirect_uri': self.REDIRECT_URI,
            'client_id': self.CONFIG['client_id'],
            'client_secret': self.CONFIG['client_secret']
        }

        _headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        _uri = self._get_oauth_uri('accessToken')

        resp = requests.post(_uri, data=_data, headers=_headers)

        if not resp.ok:
            raise RequestError(f'Fail to get access token, error is {resp.text}.')

        # get access token
        # logger.info(resp.json())
        access_token = resp.json()['access_token']
        return access_token

    def authenticate(self) -> str:
        """
        sign in linkedIn to get the user's auth token, which needs the grants from the user.
        When the user's grant is given, the dbook platform will share a text about dbook with the user's account.

        returns:
            auth_url: str, the authority url.
        """
        client_id = self.CONFIG['client_id']
        scope = 'r_liteprofile%20r_emailaddress%20w_member_social'
        auth_uri = f'https://www.linkedin.com/oauth/v2/authorization?response_type=code&' \
                   f'client_id={client_id}&redirect_uri={quote(self.REDIRECT_URI)}&state={self.STATE}&scope={scope}'
        logger.info('auth linkedIn uri ->', auth_uri)
        return auth_uri

    def get_user(self, access_token: str) -> dict:
        """
        Get user info about linkedIn, which is to link to the platform account.

        args:
            access_token: str.
        """
        _headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        _uri = self._get_uri('me')

        resp = requests.get(_uri, headers=_headers)

        if not resp.ok:
            raise RequestError(f'Cannot get user profile, error is {resp.text}')

        logger.info('linkedin user info -> ', resp.json())
        resp_data = resp.json()
        return {
            'account_id': resp_data['id'],
            'username': f'{resp_data.get("localizedFirstName", "")} {resp_data.get("localizedLastName", "")}'
        }

    def share(self, access_token: str, owner: str, content: str) -> dict:
        """
        Post a piece of text about d-book to make sure the user is real
        if an user want to be an author of the d-book platform.

        args:
            owner: str, who owns the share

            access_token: str.

            content: str, the sharing content.

        returns:
            data: dict, the data from response.
        """
        _headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        # send a share
        _data = {
            'owner': owner,
            'subject': 'DBOOK Market',
            'text': {
                'text': content,  # or text
            }
        }
        _uri = self._get_uri('shares')
        resp = requests.post(_uri, data=json.dumps(_data), headers=_headers)

        logger.info(resp, resp.json())

        if not resp.ok:
            raise RequestError(f'Fail to send share, error is {resp.text}')

        return resp.json()

    def link_user_and_share(self, wallet_addr: str, token: str, verifier: str, content: str):
        """
        Get user info to save into db and send share with the user's account.

        args:
            wallet_addr: str, the wallet address from metaMask.

            token: str, the OAuth 2.0 authorization code.

            verifier: str, A value used to test for possible CSRF attacks.

            content: str, the sharing content.
        """
        # get access token
        access_token = self.get_access_token(token, verifier)

        # get user
        sm_user = self.get_user(access_token)
        # save user
        user = User.objects.get(address=wallet_addr)
        social_media, _ = Account.objects.update_or_create(user=user, type=SocialMediaType.LINKEDIN.value,
                                                           defaults={**sm_user, **{'shared': False}})

        # send share
        self.share(access_token, f'urn:li:person:{sm_user["account_id"]}', content)

        # tag user
        social_media.shared = True
        social_media.save()
