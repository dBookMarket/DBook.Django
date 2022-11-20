import redis
import os
from django.utils import timezone
import numpy as np


class RedisHandler:

    def __init__(self):
        self.redis = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=os.getenv('REDIS_DB'))


class IssueQueue(RedisHandler):

    def __init__(self):
        super().__init__()
        self.name = 'issuing_list'

    def check_in(self, key, score):
        """

        args:
            queue: str, the collection of keys ordered by an associated score

            key: str, a member in the queue

            score: a score for the key
        """
        print(f'Put {key}-{score} into {self.name}')
        try:
            self.redis.zadd(self.name, {key: score})
        except Exception as e:
            print(f'Exception when adding a new item: {e}')
            raise

    def check_out(self):
        """
        pop a key
        """
        print(f'Remove min value from queue {self.name}')
        try:
            # self.redis.zmpop(1, [key])
            self.redis.zpopmin(self.name, 1)
        except Exception as e:
            print(f'Exception when removing an item: {e}')
            pass

    def get_top(self):
        """
        return the items whose score is less than or equal to the current timestamp
        """
        current_time = timezone.now().timestamp()
        try:
            top_list = self.redis.zrangebyscore(self.name, -np.inf, current_time)
            return list(map(lambda x: x.decode(), top_list))
        except Exception as e:
            print(f'Exception when getting top items: {e}')
            return []
