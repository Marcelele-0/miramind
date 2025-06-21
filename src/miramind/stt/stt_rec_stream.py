from .stt_stream import RecordingStream, STTStream
from queue import Queue
import threading
import time


class STTRecStream:
    rec_stream: RecordingStream
    stt_stream: STTStream
    buffer: Queue
    rec_stop_flag: threading.Event
    stt_stop_flag: threading.Event
    general_stop_flag: threading.Event = threading.Event()

    def __init__(self, **kwargs):
        self.rec_stream = RecordingStream(**kwargs)
        self.stt_stream = STTStream(target_queue=self.rec_stream.get_file_queue())
        self.buffer = self.stt_stream.get_buffer()
        self.rec_stop_flag = self.rec_stream.get_stop_flag()
        self.stt_stop_flag = self.stt_stream.get_stop_flag()

    def get_stop_flag(self):
        return self.general_stop_flag

    def get_buffer(self):
        return self.buffer

    def run(self, **kwargs):
        listening_loop = threading.Thread(target=self.rec_stream.run, kwargs=kwargs)
        transcribing_loop = threading.Thread(target=self.stt_stream.run)
        listening_loop.start()
        transcribing_loop.start()
        while not self.general_stop_flag.is_set():
            time.sleep(0.1)

        self.rec_stop_flag.set()
        listening_loop.join()
        self.stt_stop_flag.set()
        transcribing_loop.join()
