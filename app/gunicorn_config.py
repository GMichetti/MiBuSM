# Binding Flask app 
bind = '0.0.0.0:8000'

# To share workload to multilpe CPU cores (in this case 3)
workers = 2

# Using workers thread based
worker_class = 'gthread'


# Number of threads per Worker
threads = 2 

# Loading the application just one time to lower memory utilization
preload_app = True

# Opt parameters
loglevel = 'info'
accesslog = '-'
errorlog = '-'


metrics_port = 8080
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

def when_ready(server):
    GunicornPrometheusMetrics.start_http_server_when_ready(metrics_port)

def child_exit(server, worker):
    GunicornPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)