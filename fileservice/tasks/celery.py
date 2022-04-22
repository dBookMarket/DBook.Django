from celery import Celery
from .celery_config import CeleryConfig

app = Celery('file-service')
app.config_from_object(CeleryConfig)

if __name__ == '__main__':
    app.start()