import os
import redis
import time


class RedisAccessor:
    def __init__(self):
        self.conn = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=os.getenv('REDIS_DB'))

    def get_value(self, key):
        value = self.conn.get(key)
        if isinstance(value, bytes):
            return value.decode()
        return value

    def set_value(self, key, value, expire_time=0):
        self.conn.set(key, value)
        if expire_time > 0:
            self.conn.expire(key, expire_time)


class RedisLock:
    """
    todo need to optimize
    """

    def __init__(self, key):
        self.redis_accessor = RedisAccessor()
        self._lock = 0
        self.lock_key = key

    def __enter__(self, timeout=10):
        while self._lock != 1:
            timestamp = time.time() + timeout
            # 设置锁超时时间 setnx -> set if the key does not exist
            # returns:
            #   1 if the key was set
            #   0 if the key was not set
            self._lock = self.redis_accessor.conn.setnx(self.lock_key, timestamp)
            # 1, get the lock successfully
            if self._lock == 1:
                break
            else:
                # 2, 合法时间内锁不被释放，且额外增加时限后仍不会被释放，则表明线程异常无法正常释放锁
                # get the old value stored at key and set a new time
                locker_time = self.redis_accessor.conn.set(self.lock_key, timestamp, get=True)
                try:
                    locker_time = float(locker_time)
                except ValueError as e:
                    print(f'Exception when calling RedisLock.__enter__ -> {e}')
                    break
                if time.time() > locker_time:
                    break
                else:
                    time.sleep(timeout + 1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 合法时限内正常释放锁
        _value = self.redis_accessor.conn.get(self.lock_key)
        try:
            _value = float(_value)
            if time.time() > _value:
                self.redis_accessor.conn.delete(self.lock_key)
        except ValueError as e:
            print(f'Exception when calling RedisLock.__enter__ -> {e}')
            self.redis_accessor.conn.delete(self.lock_key)
