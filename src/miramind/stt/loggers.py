import logging
import os
from dotenv import load_dotenv


class SentinelLogger:
    def debug(self, *args):
        pass

    def info(self, *args):
        pass

load_dotenv()

file_handler = logging.FileHandler(f"{os.environ["LOGS_DIR"]}/stream_logs.md")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)

rec_stream_logger = logging.getLogger("rec_stream_logger")
rec_stream_logger.setLevel(logging.INFO)
rec_stream_logger.addHandler(file_handler)
rec_stream_logger.setLevel(logging.INFO)

stt_stream_logger = logging.getLogger("stt_stream_logger")
stt_stream_logger.setLevel(logging.INFO)
stt_stream_logger.addHandler(file_handler)
stt_stream_logger.setLevel(logging.INFO)
