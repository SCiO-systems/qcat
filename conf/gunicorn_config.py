command = '/usr/local/bin/gunicorn'
#pythonpath = '/code/apps' # container path
pythonpath = '/app/apps' # container path
bind = '0.0.0.0:8000'
workers = 3
