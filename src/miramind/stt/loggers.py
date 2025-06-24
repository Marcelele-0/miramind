import logging
import os
from dotenv import load_dotenv


class SentinelLogger:
    def debug(self, *args):
        pass

    def info(self, *args):
        pass


def get_loggers():
    """
    Get rec_stream_logger and stt_stream_logger.

    Returns:
        (rec_stream_logger, stt_stream_logger)
    """
    os.makedirs(f"{os.environ["LOGS_DIR"]}", exist_ok=True)
    rec_file_handler = logging.FileHandler(f"{os.environ["LOGS_DIR"]}/rec_logs.md")
    rec_file_handler.setLevel(logging.DEBUG)
    stt_file_handler = logging.FileHandler(f"{os.environ["LOGS_DIR"]}/stt_logs.md")
    stt_file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s : %(message)s", datefmt="%m-%d %H:%M:%S"
    )
    rec_file_handler.setFormatter(formatter)
    stt_file_handler.setFormatter(formatter)

    rec_stream_logger = logging.getLogger("rec_stream_logger")
    rec_stream_logger.setLevel(logging.INFO)
    rec_stream_logger.addHandler(rec_file_handler)

    stt_stream_logger = logging.getLogger("stt_stream_logger")
    stt_stream_logger.setLevel(logging.INFO)
    stt_stream_logger.addHandler(stt_file_handler)
    return rec_stream_logger, stt_stream_logger
