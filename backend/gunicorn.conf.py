"""Gunicorn configuration for BilimYol local exam server."""

import os


bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

workers = int(os.getenv("WEB_CONCURRENCY", "2"))

worker_class = "gthread"

threads = int(os.getenv("GUNICORN_THREADS", "4"))

timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5

max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
capture_output = True

# Ertangi lokal test uchun workerlar alohida ishga tushgani xavfsizroq.
preload_app = False