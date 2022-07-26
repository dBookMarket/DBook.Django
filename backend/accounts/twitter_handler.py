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

    def create_tweet(self):
        """
        post a tweet about d-book to verify the user's identity if an user want to be an author of d-book platform.
        """
        response = self.client.create_tweet(text='This is D-BOOK community.')
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

    def auth_tweet(self):
        """
        sign in twitter to get the user's auth token, which needs the authority from the user.
        """

    def list_tweets(self):
        response = self.client.search_all_tweets(query='dbook', max_results=10)
        print(response.data)


if __name__ == '__main__':
    handler = TwitterHandler()
    handler.list_tweets()
