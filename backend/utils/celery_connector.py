from celery import Celery
import logging


class CeleryConnector:

    def __init__(self, app: str, **kwargs):
        self.celery = Celery(app, **kwargs)
        self.logger = logging.getLogger(__name__)

    def send_async_task(self, task: str, *args):
        """
        :param task: str, task name
        :param args: tuple, parameters of task
        :return: AsyncResult or None
        """
        try:
            return self.celery.send_task(task, *args)
        except Exception as e:
            self.logger.error(e)
            return None

    def send_task(self, task: str, *args):
        try:
            return self.send_async_task(task, *args).get()
        except Exception as e:
            self.logger.error(e)
            return None

    def get_async_result(self, task_id: str):
        try:
            return self.celery.AsyncResult(task_id)
        except Exception as e:
            self.logger.error(e)
            return None

    def revoke_task(self, task_id: str):
        try:
            result = self.get_async_result(task_id)
            if result is not None:
                result.revoke()
        except Exception as e:
            self.logger.error(f"Fail to revoke task({task_id}), error: {e}")
