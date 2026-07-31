"""Gunicorn defaults for BilimYol production.

Render start command `gunicorn config.wsgi:application` bo‘lsa, Gunicorn
joriy backend papkasidagi ushbu config faylni avtomatik o‘qiydi.
"""

import os


bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
capture_output = True
preload_app = True
