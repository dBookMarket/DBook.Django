ARG NGINX_VERSION=${NGINX_VERSION}
FROM nginx:${NGINX_VERSION}

COPY ./html /usr/share/nginx/html

RUN mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak

ARG NGINX_CONFIG_TYPE=${NGINX_CONFIG_TYPE}
COPY ./conf/nginx_${NGINX_CONFIG_TYPE}.conf /etc/nginx/conf.d/