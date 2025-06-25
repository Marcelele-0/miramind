from stt.stt_stream import RecSTTStream
from shared.utils import get_azure_openai_client
from stt.loggers import get_loggers
import time


def test():
    rec_logger, stt_logger = get_loggers()
    client = get_azure_openai_client()
    stream = RecSTTStream(duration=3, client=client, stt_logger=stt_logger, rec_logger=rec_logger)
    stream.start()

    for i in range(5):
        time.sleep(1)

    stream.stop()
    while not stream.buffer.empty():
        stream.buffer.get()
    assert stream.buffer.empty()
