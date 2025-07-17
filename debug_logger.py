# debug_logger.py

import os
from datetime import datetime

# Path to debug log file
DEBUG_LOG_PATH = "logs/debug.log"

# Ensure log directory exists
os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)


def log_debug(msg: object) -> None:
    """
    Appends a UTC-timestamped debug message to logs/debug.log.
    Silent by default. No console output.
    """
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"[{timestamp}] DEBUG: {msg}\n"
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)


def log_error(message: str) -> None:
    """
    Appends a UTC-timestamped error message to logs/debug.log.
    Prefixes the message with ERROR.
    """
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"[{timestamp}] ERROR: {message}\n"
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)
