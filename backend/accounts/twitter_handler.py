import tweepy

# from django.conf import settings

TWITTER_CONF = {
    'consumer_key': 'aJU6ezXXuulitBqN1CpPOM2gP',
    'consumer_secret': '0He7QNiUVRthUGbeq8LdcTy620uNjGe06YMDzrLR6MUtcfmctK',
    'access_token': '1391642292864249856-TFrpdLdJX6mmdQWKU2u7gnPimKv68C',
    'access_token_secret': 'FRe5kkNR25V3ZY73nhYcOfrTsNMEImtXv8AetqKPCBAtj',
    'bearer_token': 'AAAAAAAAAAAAAAAAAAAAAOu2fAEAAAAAiIAyhKgMggc3EG%2BMWkijcCPccY4%3DAl40Jj0XetJANnhNtCknYIftlqL8t1ybxdWSFvqI7ALrYt9XTc'
}


class TwitterHandler(object):
    """
    This class is for calling the twitter's api to read and write the tweets. The version of twitter api is v2.
    """

    def __init__(self):
        self.client = tweepy.Client(bearer_token=TWITTER_CONF['bearer_token'],
                                    consumer_key=TWITTER_CONF['consumer_key'],
                                    consumer_secret=TWITTER_CONF['consumer_secret'],
                                    access_token=TWITTER_CONF['access_token'],
                                    access_token_secret=TWITTER_CONF['access_token_secret'])
        self.oauth_user_handler = tweepy.OAuth1UserHandler(TWITTER_CONF['consumer_key'], TWITTER_CONF['consumer_secret'])

    def create_tweet(self, oauth_verifier: str):
        """
        post a tweet about d-book to make sure the user is real if an user want to be an author of the d-book platform.

        args:
        	oauth_verifier: str, which is to get the user's access token and secret.

        """
        # get user's access token and secret
        access_token, access_token_secret = self.oauth_user_handler.get_access_token(oauth_verifier)
        user_client = tweepy.Client(consumer_key=TWITTER_CONF['consumer_key'],
                                    consumer_secret=TWITTER_CONF['consumer_secret'],
                                    access_token=access_token,
                                    access_token_secret=access_token_secret)
        # create a tweet
        response = user_client.create_tweet(text='This is D-BOOK community.')
        print(response)

    def check_tweet(self, user_id: str) -> bool:
        """
        check if the user post the tweet about d-book. Call search_recent_tweets() to get the recent tweets from the user.
        If the

        args:
            user_id: str, the user id of twitter account.

        returns:
            bool, if the user posted the tweet, return True, or return False
        """
        pass


    def auth_tweet(self) -> str:
        """
        sign in twitter to get the user's auth token, which needs the grants from the user.
        When the user's grant is given, the dbook platform will post a tweet about dbook with the user's account.

        returns:
        	str, the authority url from the user.
        """
        oauth1_user_handler = tweepy.OAuth1UserHandler(TWITTER_CONF['consumer_key'], TWITTER_CONF['consumer_secret'])
        auth_url = oauth1_user_handler.get_authorization_url()
        print('auth url->', auth_url)
        return auth_url


    def list_tweets(self):
        response = self.client.search_recent_tweets(query='from:ddid_io', max_results=10)
        print(response.data)


if __name__ == '__main__':
    handler = TwitterHandler()
    # handler.list_tweets()
    handler.auth_tweet()
