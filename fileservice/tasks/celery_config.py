# from celery.schedules import crontab
import os


class CeleryConfig:
    # timezone = 'Asia/Shanghai'
    broker_url = f'pyamqp://{os.getenv("RABBITMQ_USER")}:{os.getenv("RABBITMQ_PASS")}@{os.getenv("RABBITMQ_HOST")}:{os.getenv("RABBITMQ_PORT")}/{os.getenv("RABBITMQ_VHOST")}'
    result_backend = f'redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/{os.getenv("REDIS_DB")}'
    include = ['tasks.main']
    task_time_limit = 60 * 60 * 2  # hard time limit 1 hour
    task_soft_time_limit = 60 * 60 * 2
    task_default_rate_limit = 10  # allow 10 tasks per minute
    worker_max_memory_per_child = 256000  # 256MB
    worker_cancel_long_running_tasks_on_connection_loss = True
    # beat_schedule = {
    #     'update-order-every-hour': {
    #         'task': 'amazon.tasks.update_updated_orders',
    #         'schedule': crontab(hour='*/1', minute=0) # every one hour, like 0am, 1am, 2am, 3am, 4am, ...
    #     }
    # }