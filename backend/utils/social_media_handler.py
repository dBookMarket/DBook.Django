import tweepy
from accounts.models import User, SocialMedia
from utils.enums import SocialMediaType
import requests
import json

from django.conf import settings


class SocialMediaFactory(object):

    @classmethod
    def get_instance(cls, _type: str):
        if _type == 'twitter':
            return TwitterHandler()
        if _type == 'linkedin':
            return LinkedInHandler()
        return None


class DuplicationError(Exception):
    pass


class RequestError(Exception):
    pass


class SocialMediaHandler(object):
    """
    Social Media Account base handler class.
    """
    REDIRECT_URI = 'https://testnet.dbookmarket.com/sharing'

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

        _headers = {
            'Content_Type': 'application/x-www-form-urlencoded'
        }

        _uri = self._get_oauth_uri('access_token')

        resp = requests.post(_uri, data=_data, headers=_headers)

        print('response from access token api ->', resp, resp.text, resp.content)

        if resp.status_code < 200 or resp.status_code >= 300:
            raise RequestError('Fail to get access token, please try later...')

        try:
            resp_data = resp.json()
        except requests.exceptions.JSONDecodeError as e:
            print(f'Exception when calling TwitterHandler.get_access_token -> {e}')
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
            print(f'Exception when calling TwitterHandler.get_user -> {e}')
            raise RequestError('Fail to get user profile, please ask manager for help.')

        if resp.status_code < 200 or resp.status_code >= 300:
            raise RequestError(f'Fail to get user profile, status code is {resp.status_code}')

        return {
            'account_id': resp.data['id'],
            'username': resp.data['username']
        }

    def share(self, access_token: str, access_token_secret: str) -> dict:
        """
        post a tweet about d-book to make sure the user is real if an user want to be an author of the d-book platform.

        args:
            access_token: str, from get_access_token()

            access_token_secret: str, from get_access_token()

        returns:
            data: dict, the data from response.
        """
        user_client = tweepy.Client(consumer_key=self.CONFIG['consumer_key'],
                                    consumer_secret=self.CONFIG['consumer_secret'],
                                    access_token=access_token,
                                    access_token_secret=access_token_secret)
        # create a tweet
        try:
            resp = user_client.create_tweet(text='This is a D-BOOK community.@ddid_io')
        except tweepy.errors.Forbidden as e:
            print(f'Exception when calling TwitterHandler.share -> {e}')
            raise DuplicationError('You already tweet one.')
        except Exception as e:
            print(f'Exception when calling TwitterHandler.share -> {e}')
            raise RequestError('Fail to send share, please try later...')

        if resp.status_code < 200 or resp.status_code >= 300:
            raise RequestError(f'Fail to send share, status code is {resp.status_code}')

        return resp.data

    def authenticate(self) -> str:
        """
        sign in twitter to get the user's auth token, which needs the grants from the user.
        When the user's grant is given, the dbook platform will post a tweet about dbook with the user's account.

        returns:
            auth_url: str, the authority url from the user.
        """
        oauth_user_handler = tweepy.OAuth1UserHandler(self.CONFIG['consumer_key'],
                                                      self.CONFIG['consumer_secret'])
        try:
            auth_url = oauth_user_handler.get_authorization_url(signin_with_twitter=True)
        except Exception as e:
            print(f'Exception when calling TwitterHandler.authenticate -> {e}')
            raise RequestError('Fail to authenticate, please try later...')
        print('auth url->', auth_url)
        return auth_url

    def link_user_and_share(self, wallet_addr: str, token: str, verifier: str):
        """
        Get user info to save into db and send share with the user's account.

        args:
            wallet_addr: str, the wallet address from metaMask.

            token: str, which is from the redirect uri when the user granted.

            verifier: str, which is from the redirect uri when the user granted.
        """
        # get access token
        access_token, access_token_secret = self.get_access_token(token, verifier)

        # get user info
        sm_user = self.get_user(access_token, access_token_secret)
        # save user
        user = User.objects.get(account_addr=wallet_addr)
        social_media, _ = SocialMedia.objects.get_or_create(user=user, type=SocialMediaType.TWITTER.value,
                                                            defaults={**sm_user, **{'shared': False}})

        # send share
        self.share(access_token, access_token_secret)

        # tag user
        social_media.shared = True
        social_media.save()


class LinkedInHandler(SocialMediaHandler):
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

        if resp.status_code < 200 or resp.status_code >= 300:
            raise RequestError(f'Fail to get access token, status code is {resp.status_code}.')

        # get access token
        # print(resp.json())
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
                   f'client_id={client_id}&redirect_uri={self.REDIRECT_URI}&state={self.STATE}&scope={scope}'
        print('auth linkedIn uri ->', auth_uri)
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

        if resp.status_code < 200 or resp.status_code >= 300:
            raise RequestError(f'Cannot get user profile, status code is {resp.status_code}')

        print('linkedin user info -> ', resp.json())
        resp_data = resp.json()
        return {
            'account_id': resp_data['id']
        }

    def share(self, access_token: str, owner: str) -> dict:
        """
        Post a piece of text about d-book to make sure the user is real
        if an user want to be an author of the d-book platform.

        args:
            owner: str, who owns the share

            access_token: str.

        returns:
            data: dict, the data from response.
        """
        _headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        # send a share
        # todo content is from frontend?
        _data = {
            'owner': owner,
            'subject': 'DBOOK',
            'text': {
                'text': 'This is a D-BOOK community.@ddid_io',  # or text
            }
        }
        _uri = self._get_uri('shares')
        resp = requests.post(_uri, data=json.dumps(_data), headers=_headers)

        print(resp, resp.json())

        if resp.status_code < 200 or resp.status_code >= 300:
            raise RequestError(f'Fail to send share, status code is {resp.status_code}')

        return resp.json()

    def link_user_and_share(self, wallet_addr: str, token: str, verifier: str):
        """
        Get user info to save into db and send share with the user's account.

        args:
            wallet_addr: str, the wallet address from metaMask.

            token: str, the OAuth 2.0 authorization code.

            verifier: str, A value used to test for possible CSRF attacks.
        """
        # get access token
        access_token = self.get_access_token(token, verifier)

        # get user
        sm_user = self.get_user(access_token)
        # save user
        user = User.objects.get(account_addr=wallet_addr)
        social_media, _ = SocialMedia.objects.get_or_create(user=user, type=SocialMediaType.LINKEDIN.value,
                                                            defaults={**sm_user, **{'shared': False}})

        # send share
        self.share(access_token, f'urn:li:person:{sm_user["account_id"]}')

        # tag user
        social_media.shared = True
        social_media.save()


if __name__ == '__main__':
    f = './obj.txt'
    # handler = TwitterHandler()
    # handler.authenticate()

    # handler.get_access_token(oauth_token='prco6AAAAAABfLbrAAABgmcYnyQ',
    #                          oauth_verifier='cHfGmcLExtvOktghX9dBS9Cq6OtltNAE')

    # access_token = '1391642292864249856-iLHQfjstAR8S1jz7LCXsSoRqQsh0qs'
    # access_token_secret = 'g0Qriog6viYrwfybFyJSYAXWTuK5RI0lggCTlmoJVtzzr'
    # # handler.link_account('abc', access_token, access_token_secret)
    #
    # handler.create_msg(access_token, access_token_secret)

    # handler = LinkedInHandler()
    # # handler.authenticate()
    #
    # code = 'AQShrRzFsAA50idAk-J9TD0f8nKyMpGGyfZwZp_mBOfCjtoqS8TXNl_GDDcqkvCRoQgtuR2ODWq7gkSuRoLgVtFpIDIYf182e31q7TzeXbsTO2LOuuXzp1Xy6eV476G0KWI-IP-IlkLShL5s3gjYthzvEv0GXr2Z4sBWGSTMpghkjJ9xY8zTFKI5XEddxftWwwzbPHimldkVRuLfinE'
    # state = 'rwer243fa2sfse'
    # # handler.create_msg('aaa',
    # #                    'AQSdacRc2adCH623M5VCNCAgxQkMbiMBf__f67tsxfrly0EpY0UIrfXcwiUkrsGbRQr6c2o72VxJ-HVb9yszhtI95lFiyMxA0TRCUgUS7XeC9yfTzqMjwy6EHDLZPKeCVccfzU3zLeFdVQVbqyyMbDyV2dm5UW9A4c_adb5pedEAMG9QAQ8eGcw6k0LbtVNOoDKoX3edPGZBjeIWa4U')
    # # handler.get_access_token(state, code)
    #
    # access_token = 'AQUBVnIaAdqTFlSLOKaPKgFi9JnJyTjZg25aPip00rAGI5vbPF93F_y20FRsiTf9XBvWJga6enxqTP3V4fSokv2VuP166bzIb8BcDZniufqNOeelwRoV79YGi9TJoVdSfQUGU1851it9CjNCPgDySGLcVaFWZZyWaL5w-CmOuKclW5efBL6PUBhy4ivpGInqnUFUO134iZIUzzI2Avj5XzZ68BFenX6m3NlyZpR0IkqmjChoduBMwK5w3DD3D930fLFSJUN6wWmLTRESN2ShGcSiDXbVR9j9Ow-dzlGR2Ddh83j_A21ec0Nyr_xmM0HPRsd5Bdx_2xpsfZyGZkyPtSxIO2-djg'
    # # handler.get_user(access_token)
    # handler.share(access_token)
