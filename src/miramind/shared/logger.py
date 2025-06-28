import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LOG_FILE = os.getenv("LOG_FILE", os.path.join(ROOT_DIR, "logs", "miramind.log"))

# Ensure the logs directory exists at the project root
log_dir = os.path.dirname(LOG_FILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# Create logger
logger = logging.getLogger("miramind")
logger.setLevel(LOG_LEVEL)
logger.propagate = False

# Formatter
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Rotating file handler
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Quick function to get logger in other modules
get_logger = logging.getLogger

# Example usage (best practice):
# from src.miramind.shared.logger import logger
# logger.info("This is an info message.")
# logger.error("This is an error message.")
# logger.debug("This is a debug message.")