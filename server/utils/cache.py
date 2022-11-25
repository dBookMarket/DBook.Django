import datetime
import logging
import os


class Cache:

    def __init__(self, session):
        self.expiry_suffix = 'expiry_time'
        self.session = session
        self.logger = logging.getLogger(__name__)

    def set(self, key, value, expiry_time=3600):
        """
        :param key: str
        :param value: auto
        :param expiry_time: int, seconds, default 1 hour
        :return:
        """
        try:
            now = datetime.datetime.now()
            self.session[key] = value
            self.session[f"{key}_{self.expiry_suffix}"] = (now + datetime.timedelta(seconds=expiry_time)).timestamp()
        except Exception as e:
            self.logger.error(f'Fail to set cache, error: {e}')

    def get(self, key):
        try:
            now = datetime.datetime.now().timestamp()
            expiry_time = self.session[f"{key}_{self.expiry_suffix}"]
            if expiry_time >= now:
                return self.session[key]
            # time out, remove cache
            self.remove(key)
            return None
        except Exception as e:
            self.logger.error(f'Fail to get cache, error: {e}')
            self.remove(key)
            return None

    def remove(self, key):
        value = self.session[key]
        if value and os.path.isfile(value):
            os.remove(value)
        self.session.pop(key, None)
        self.session.pop(f"{key}_{self.expiry_suffix}", None)

    def clear(self):
        self.session.clear()
