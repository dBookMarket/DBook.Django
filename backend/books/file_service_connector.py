from utils.celery_connector import CeleryConnector
import os
from .file_service_config import FileServiceConfig


class FileServiceConnector(CeleryConnector):
    def __init__(self):
        broker = f'pyamqp://{os.getenv("RABBITMQ_USER")}:{os.getenv("RABBITMQ_PASS")}@{os.getenv("RABBITMQ_HOST")}:{os.getenv("RABBITMQ_PORT")}/{os.getenv("RABBITMQ_VHOST")}'
        backend = f'redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/{os.getenv("REDIS_DB")}'
        super().__init__(FileServiceConfig.APP, broker=broker, backend=backend)

    def upload_file(self, file_path: str):
        result = self.send_async_task(FileServiceConfig.TASK_UPLOAD_FILE, (file_path,))
        return result

    def get_file_urls(self, cid):
        urls = self.send_task(FileServiceConfig.TASK_GET_FILE_URLS, (cid,))
        return urls
