import multiprocessing

bind = "0.0.0.0:8000"
workers = 4
capture_output = True
# proc_name = 'django_worker'
# errorlog = 'logs/gunicorn.log'
worker_class = 'gevent'
