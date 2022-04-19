#!/bin/bash

python manage.py makemigrations

python manage.py migrate --fake-initial

#python manage.py loaddata db_data.json

python manage.py autocreatesuperuser ${ADMIN_NAME} ${ADMIN_PASSWORD} ${ADMIN_EMAIL}

python manage.py collectstatic --no-input

#python manage.py runserver 0.0.0.0:8000
#gunicorn -c core/gunicorn.py core.wsgi
supervisord -c /code/supervisord.conf
