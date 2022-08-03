import tweepy
# import pickle
from accounts.models import User, SocialMedia
from utils.enums import SocialMediaAccountType
import requests

from django.conf import settings


class SocialMediaFactory(object):

    @classmethod
    def get_instance(cls, _type: str):
        if _type == 'twitter':
            return TwitterHandler()
        if _type == 'linkedin':
            return LinkedInHandler()
        return None


class SMAccountHandler(object):
    """
    Social Media Account base handler class.
    """
    REDIRECT_URI = 'https://testnet.dbookmarket.com/sharing'

    def create_msg(self, **kwargs):
        pass

    def authenticate(self):
        pass

    def verify_msg(self, **kwargs):
        pass


class DuplicationError(Exception):
    pass


class TwitterHandler(SMAccountHandler):
    """
    This class is for calling the twitter's api to read and write the tweets. The version of twitter api is v2.
    """
    TWITTER_CONF = settings.TWITTER_SETTINGS

    def __init__(self):

        self.client = tweepy.Client(bearer_token=self.TWITTER_CONF['bearer_token'],
                                    consumer_key=self.TWITTER_CONF['consumer_key'],
                                    consumer_secret=self.TWITTER_CONF['consumer_secret'],
                                    access_token=self.TWITTER_CONF['access_token'],
                                    access_token_secret=self.TWITTER_CONF['access_token_secret'])

    def get_access_token(self, oauth_token: str, oauth_verifier: str) -> (str, str):
        """
        Get the user's oauth token, which is granted by him/her.

        args:
            oauth_token: str, which is from the redirect uri when the user granted.
            oauth_verifier: str, which is from the redirect uri when the user granted.

        returns:
            access_token: str,
            access_token_secret: str
        """
        data = {
            'oauth_consumer_key': self.TWITTER_CONF['consumer_key'],
            'oauth_token': oauth_token,  # or passed from frontend
            'oauth_verifier': oauth_verifier
        }

        resp = requests.post('https://api.twitter.com/oauth/access_token', data=data)

        if resp.status_code == 200:
            return resp.json()['oauth_token'], resp.json()['oauth_token_secret']

        return '', ''

    def link_account(self, account_addr: str, access_token: str, access_token_secret: str):
        """
        Link the user's twitter account to the dbook platform account, which is to check the user's identity.

        args:
            account_addr: str, the user's wallet address which is linked to the user's platform account.

            access_token: str, from get_access_token()

            access_token_secret: str, from get_access_token()
        """
        user_client = tweepy.Client(consumer_key=self.TWITTER_CONF['consumer_key'],
                                    consumer_secret=self.TWITTER_CONF['consumer_secret'],
                                    access_token=access_token,
                                    access_token_secret=access_token_secret)
        # get user's id to store into db, which links to the user's platform account.
        resp = user_client.get_me()
        user = User.objects.get(account_addr=account_addr)
        SocialMedia.objects.get_or_create(user=user, type=SocialMediaAccountType.TWITTER.value,
                                          account_id=resp.data['id'])

    def create_msg(self, access_token: str, access_token_secret: str) -> dict:
        """
        post a tweet about d-book to make sure the user is real if an user want to be an author of the d-book platform.

        args:
            access_token: str, from get_access_token()

            access_token_secret: str, from get_access_token()

        returns:
            data: dict, the data from response.
        """
        # get user's access token and secret
        # access_token, access_token_secret = self.oauth_user_handler.get_access_token(oauth_verifier)
        print(access_token, access_token_secret)
        user_client = tweepy.Client(consumer_key=self.TWITTER_CONF['consumer_key'],
                                    consumer_secret=self.TWITTER_CONF['consumer_secret'],
                                    access_token=access_token,
                                    access_token_secret=access_token_secret)
        # create a tweet
        try:
            response = user_client.create_tweet(text='This is a D-BOOK community.@ddid_io')
            print(response)
            return response.data
        except tweepy.errors.Forbidden as e:
            print(f'Exception when calling create_tweet -> {e}')
            raise DuplicationError('You already tweet one.')

    # def verify_msg(self, account_addr: str) -> bool:
    #     """
    #     check if the user post the tweet about d-book. Call search_recent_tweets() to get the recent tweets from the user.
    #     If the
    #
    #     args:
    #         account_addr: str, the user's wallet account address.
    #
    #     returns:
    #         bool, if the user posted the tweet, return True, or return False
    #     """
    #     sma = SocialMedia.objects.get(user__account_addr=account_addr, type=SocialMediaAccountType.TWITTER.value)
    #     resp = self.client.search_recent_tweets(query=f'@ddid_io from:{sma.account_id}')
    #     return bool(resp.data)

    def authenticate(self) -> str:
        """
        sign in twitter to get the user's auth token, which needs the grants from the user.
        When the user's grant is given, the dbook platform will post a tweet about dbook with the user's account.

        returns:
            auth_url: str, the authority url from the user.
        """
        # get oauth token
        # data = {
        #     'oauth_callback': self.REDIRECT_URI,
        #     'oauth_consumer_key': self.TWITTER_CONF['consumer_key']
        # }
        # resp = requests.post('https://api.twitter.com/oauth/request_token', data=data)
        #
        # if resp.status_code != 200:
        #     raise ValueError()
        #
        # resp_data = resp.json()
        # if not resp_data['oauth_callback_confirmed']:
        #     raise ValueError()
        #
        # oauth_token = resp_data['oauth_token']
        # auth_url = f'https://api.twitter.com/oauth/authorize?oauth_token={oauth_token}'
        oauth_user_handler = tweepy.OAuth1UserHandler(self.TWITTER_CONF['consumer_key'],
                                                      self.TWITTER_CONF['consumer_secret'])
        auth_url = oauth_user_handler.get_authorization_url(signin_with_twitter=True)
        print('auth url->', auth_url)
        return auth_url

    def list_tweets(self):
        response = self.client.search_recent_tweets(query='This is a D-BOOK community', max_results=10)
        print(response.data)

    def get_me(self):
        response = self.client.get_me(user_fields=['id', 'name', 'verified'])
        print(response)


class LinkedInHandler(SMAccountHandler):
    CONFIG = settings.LINKEDIN_SETTINGS
    REDIRECT_URI = 'https://testnet.dbookmarket.com/sharing'

    def authenticate(self) -> str:
        """
        sign in linkedIn to get the user's auth token, which needs the grants from the user.
        When the user's grant is given, the dbook platform will share a text about dbook with the user's account.

        returns:
            auth_url: str, the authority url.
        """
        client_id = self.CONFIG['client_id']
        state = 'rwer243fa2sfse'
        scope = 'r_liteprofile%20r_emailaddress%20w_member_social'
        auth_url = f'https://www.linkedin.com/oauth/v2/authorization?response_type=code&' \
                   f'client_id={client_id}&redirect_uri={self.REDIRECT_URI}&state={state}&scope={scope}'
        return auth_url

    def create_msg(self, account_addr: str, oauth_verifier: str) -> dict:
        """
        Post a piece of text about d-book to make sure the user is real if an user want to be an author of the d-book platform.

        args:
            oauth_verifier: str, which is to get the user's access token.

            account_addr: str, the user's wallet address which is linked to the user's platform account.

        returns:
            data: dict, the data from response.
        """
        data = {
            'grant_type': 'authorization_code',
            'code': oauth_verifier,
            'redirect_uri': self.REDIRECT_URI,
            'client_id': self.CONFIG['client_id'],
            'client_secret': self.CONFIG['client_secret']
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        api = 'https://www.linkedin.com/oauth/v2/accessToken'

        resp = requests.post(api, data=data, headers=headers)

        if resp.status_code == 400:
            raise ValueError('The authorization code is expired, please grant again.')
        # get access token
        print(resp.json())
        access_token = resp.json()['access_token']

        auth_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        # get user's info and save into db
        resp = requests.get('https://api.linkedin.com/v2/me', headers=auth_headers)
        print(resp.json())

        # send a share
        # todo content is from frontend?
        data = {
            'owner': 'urn',
            'subject': '',
            'content': '',  # or text
        }
        resp = requests.post('https://api.linkedin.com/v2/shares', data=data, headers=auth_headers)

        return resp.json()


if __name__ == '__main__':
    f = './obj.txt'
    handler = TwitterHandler()
    # handler.list_tweets()
    handler.authenticate()
    # with open(f, 'wb') as _f:
    #     pickle.dump(handler, _f)

    # with open(f, 'rb') as _f:
    #     handler = pickle.load(_f)
    # if handler:
    #     handler.create_tweet('2HCWSGOLT6LNJq9LHKml5Bul3bvF1BM8')
    # else:
    #     print('handler is not object', handler)

    # handler = TwitterHandler()
    # handler.list_tweets()

    # handler = TwitterHandler()
    # handler.get_me()

    # handler = LinkedInHandler()
    # handler.create_msg('aaa',
    #                    'AQSdacRc2adCH623M5VCNCAgxQkMbiMBf__f67tsxfrly0EpY0UIrfXcwiUkrsGbRQr6c2o72VxJ-HVb9yszhtI95lFiyMxA0TRCUgUS7XeC9yfTzqMjwy6EHDLZPKeCVccfzU3zLeFdVQVbqyyMbDyV2dm5UW9A4c_adb5pedEAMG9QAQ8eGcw6k0LbtVNOoDKoX3edPGZBjeIWa4U')
