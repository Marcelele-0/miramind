import logging
from stt.sttstream import RecordingStream

if __name__ == "__main__":
    logger = logging.getLogger("My logger")
    logger.setLevel(logging.INFO)
    logger.info("start")
    print("kkkk")
    RecordingStream.record(settings={"duration": 10}, logger=logger)
