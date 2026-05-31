bind = "0.0.0.0:" + __import__("os").environ.get("PORT", "8080")
workers = 1
timeout = 600
graceful_timeout = 600
preload_app = True
worker_class = "sync"
