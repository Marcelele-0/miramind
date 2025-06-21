import logging


class SentinelLogger:
    def debug(self, *args):
        pass

    def info(self, *args):
        pass


rec_stream_logger = logging.getLogger("rec_stream_logger")
rec_stream_logger.setLevel(logging.INFO)

stt_stream_logger = logging.getLogger("stt_stream_logger")
stt_stream_logger.setLevel(logging.INFO)