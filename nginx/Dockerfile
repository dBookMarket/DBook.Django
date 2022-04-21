ARG NGINX_VERSION=${NGINX_VERSION}
FROM nginx:${NGINX_VERSION}

RUN mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak

ARG NGINX_CONFIG_TYPE=${NGINX_CONFIG_TYPE}
COPY ./nginx/nginx_${NGINX_CONFIG_TYPE}.conf /etc/nginx/conf.d/