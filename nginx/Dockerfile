ARG NGINX_VERSION=${NGINX_VERSION}
FROM nginx:${NGINX_VERSION}

RUN mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak
COPY ./nginx/nginx.conf /etc/nginx/conf.d/