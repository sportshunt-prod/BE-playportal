# Gunicorn configuration file
import os
from pathlib import Path

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Process naming
proc_name = "sportshunt"

# Server mechanics
daemon = False
pidfile = None
tmp_upload_dir = None

# SSL (uncomment for HTTPS)
# keyfile = None
# certfile = None

# Environment
def when_ready(server):
    """Called just after the server is started."""
    # Ensure logs directory exists
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    server.log.info("Logs directory ensured at: %s", logs_dir)

def worker_int(worker):
    """Called just after a worker has been killed by a signal."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)
