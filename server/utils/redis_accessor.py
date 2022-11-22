import os
import redis
import time


class RedisLock:
    def __init__(self, key):
        self.redis_accessor = RedisAccessor()
        self._lock = 0
        self.lock_key = key

    def __enter__(self, timeout=10):
        while self._lock != 1:
            timestamp = time.time() + timeout + 1
            # 设置锁超时时间
            self._lock = self.redis_accessor.conn.setnx(self.lock_key, timestamp)
            # 1, 正常获取到锁
            # 2, 合法时间内锁为被释放，且额外增加时限后仍不会被释放，则表明线程异常无法正常释放锁
            if self._lock == 1 or (time.time() > self.redis_accessor.conn.get(
                    self.lock_key) and time.time() > self.redis_accessor.conn.getset(self.lock_key, timestamp)):
                break
            else:
                time.sleep(0.3)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 合法时限内正常释放锁
        if time.time() > self.redis_accessor.conn.get(self.lock_key):
            self.redis_accessor.conn.delete(self.lock_key)


class RedisAccessor:
    def __init__(self):
        self.conn = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=os.getenv('REDIS_DB'))

    def get_value(self, key):
        value = self.conn.get(key)
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        return value

    def set_value(self, key, value, expire_time=0):
        self.conn.set(key, value)
        if expire_time > 0:
            self.conn.expire(key, expire_time)
