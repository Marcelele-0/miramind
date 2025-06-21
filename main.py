import time
import logging

t = time.time()
from stt.stt_stream import RecordingStream
print(f'Import time: {time.time() - t}')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    t = time.time()
    logger = logging.getLogger("My_logger")
    logger.setLevel(logging.INFO)
    logger.info("start")
    RecordingStream.record(logger=logger, duration=10)
    print(f'Execution time: {time.time() - t}')
