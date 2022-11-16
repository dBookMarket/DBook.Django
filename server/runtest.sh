#!/bin/bash

python manage.py makemigrations

python manage.py migrate --fake-initial

python manage.py autocreatesuperuser ${ADMIN_NAME} ${ADMIN_PASSWORD} ${ADMIN_EMAIL}

pytest tests