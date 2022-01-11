command = '/usr/local/bin/gunicorn'
#pythonpath = '/code/apps' # host path
pythonpath = '/app/apps' # container path
bind = '0.0.0.0:8000'
workers = 3

timeout = 999

errorlog = '-'
loglevel = 'debug'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
