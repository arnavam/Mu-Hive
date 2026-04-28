# logger_config.py
import logging
import os
import sys
import time

_start_time = time.time()
_configured = False

def reset_timer():
    global _start_time
    _start_time = time.time()

class ElapsedTimeFormatter(logging.Formatter):
    def format(self, record):
        elapsed = time.time() - _start_time
        record.elapsed = f"{elapsed:.2f}s"
        return super().format(record)

def setup_logging():
    """Call this once at application startup."""
    global _configured
    if _configured:
        return
    log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper())
    formatter = ElapsedTimeFormatter('[%(elapsed)s] -- %(filename)s -- %(message)s')
    root = logging.getLogger()
    root.setLevel(log_level)
    # Remove any default handlers (optional)
    for h in root.handlers[:]:
        root.removeHandler(h)
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    _configured = True

def get_logger(name: str) -> logging.Logger:
    """Just returns a logger – all config already done."""
    return logging.getLogger(name)
