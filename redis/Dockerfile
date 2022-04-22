ARG REDIS_VERSION=${REDIS_VERSION}
FROM redis:${REDIS_VERSION}

WORKDIR /redis

COPY redis.conf /usr/local/etc/redis/redis.conf
#CMD [ "redis-server", "/usr/local/etc/redis/rabbitmq.conf" ]
#CMD [ "redis-server" ]

COPY start.sh ./
RUN chmod +x start.sh