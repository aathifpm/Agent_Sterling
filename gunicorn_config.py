workers = 4
worker_class = 'uvicorn.workers.UvicornWorker'
bind = '0.0.0.0:10000'
keepalive = 120
errorlog = '-'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' 