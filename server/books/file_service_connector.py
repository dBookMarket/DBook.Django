from utils.celery_connector import CeleryConnector
import os
import uuid
from django.conf import settings
from .file_service_config import FileServiceConfig


class FileServiceConnector(CeleryConnector):
    def __init__(self):
        # broker = f'pyamqp://{os.getenv("RABBITMQ_USER")}:{os.getenv("RABBITMQ_PASS")}@{os.getenv("RABBITMQ_HOST")}:{os.getenv("RABBITMQ_PORT")}/{os.getenv("RABBITMQ_VHOST")}'
        broker = f'redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/{os.getenv("REDIS_DB")}'
        backend = f'redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/{os.getenv("REDIS_DB")}'
        super().__init__(FileServiceConfig.APP, broker=broker, backend=backend)

    def upload_file(self, file_path: str):
        result = self.send_async_task(FileServiceConfig.TASK_UPLOAD_FILE, (file_path,))
        return result

    def get_file_urls(self, cids: list):
        urls = self.send_task(FileServiceConfig.TASK_GET_FILE_URLS, (cids,))
        return urls

    def download_file(self, cid: str, key: str, file_type: str):
        filename = f'{uuid.uuid4().hex}.{file_type}.bin'
        file_path = os.path.join(settings.TEMPORARY_ROOT, filename)
        res = self.send_task(FileServiceConfig.TASK_DOWNLOAD_FILE, (file_path, cid, key))
        # remove encrypted file
        os.remove(file_path)
        return res
