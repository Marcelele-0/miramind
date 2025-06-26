from stt.stt_stream import RecSTTStream
from stt.loggers import get_loggers
import time


def test():
    rec_logger, stt_logger = get_loggers()
    client = None
    stream = RecSTTStream(duration=3, client=client, stt_logger=stt_logger, rec_logger=rec_logger)
    stream.start()

    for i in range(5):
        time.sleep(1)

    stream.stop()
    collected_transcripts = []
    while not stream.buffer.empty():
        collected_transcripts.append(stream.buffer.get())
    assert stream.buffer.empty()
