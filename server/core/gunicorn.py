import multiprocessing

bind = "0.0.0.0:8000"
workers = 4
capture_output = True
# proc_name = 'django_worker'
# errorlog = 'logs/gunicorn.log'
worker_class = 'gevent'
# error
# [CRITICAL] WORKER TIMEOUT (pid:211)
# [WARNING] Worker with pid 211 was terminated due to signal 9
timeout = 300  # 5 minutes
