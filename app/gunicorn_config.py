try:
    from config_loader import Config_Loader
except ModuleNotFoundError:
    from .config_loader import Config_Loader


config_loader = Config_Loader()

GUNICORN_BIND = config_loader.config["gunicorn_bind"]
WORKERS = config_loader.config["gunicorn_workers"]
WORKERS_CLASS = config_loader.config["gunicorn_worker_class"]
WORKERS_THREAD = config_loader.config["gunicorn_workers_thread"]


# Binding Flask app 
bind = GUNICORN_BIND

# To share workload to multilpe CPU cores
workers = WORKERS

# Using workers thread based
worker_class = WORKERS_CLASS

# Number of threads per Worker
threads = WORKERS_THREAD

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