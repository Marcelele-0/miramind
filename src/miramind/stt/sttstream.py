import sounddevice as sd
from scipy.io.wavfile import write
from stt import STT
from queue import Queue
from dotenv import load_dotenv
import threading
import os
import time
import logging
import uuid
import base64


logging.basicConfig(level=logging.WARNING)

rec_stream_logger = logging.getLogger("rec_stream_logger")
rec_stream_logger.setLevel(logging.INFO)

stt_stream_logger = logging.getLogger("stt_stream_logger")
stt_stream_logger.setLevel(logging.INFO)
load_dotenv()


def get_short_uuid():
    u = uuid.uuid4()
    return base64.urlsafe_b64encode(u.bytes).rstrip(b'=').decode('ascii')


class RecordingStream:
    file_queue: Queue
    temp_dir: str
    stop_flag: threading.Event = threading.Event()

    def __init__(self, file_queue: Queue = None, temp_dir: str = "sttr_temp", **kwargs):
        if file_queue is None:
            file_queue = Queue()

        self.file_queue = file_queue
        self.temp_dir = f"{os.environ["MIRAMIND_TEMP"]}/{temp_dir}"

    def get_queue(self):
        return self.file_queue
    
    def get_stop_flag(self):
        return self.stop_flag

    @staticmethod
    def record(path: str = "output.wav", settings: dict = None, verbose: bool = False):
        if settings is None:
            settings = {}
        duration = settings.get("duration", 3)
        sample_rate = settings.get("sample_rate", 44100 )

        if verbose:
            print("Recording...")
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2)
        sd.wait()

        write(path, sample_rate, audio)
        if verbose:
            print(f"Recording saved to {path}")
    
    def run(self, **kwargs):
        while not self.stop_flag.is_set():
            t = time.time()
            path = f"{self.temp_dir}/{get_short_uuid()}.wav"
            rec_stream_logger.info("Recording...")
            self.record(path=path, settings=kwargs)
            self.file_queue.put(path)
            rec_stream_logger.info(f"Recording completed. Time elapsec: {time.time() - t}.")


class STTStream:
    target_queue: Queue
    stt: STT = STT()
    buffer: Queue = Queue()
    stop_flag: threading.Event = threading.Event()

    def __init__(self, target_queue):
        self.target_queue = target_queue

    def get_stop_flag(self):
        return self.stop_flag
    
    def get_buffer(self):
        return self.buffer

    def transcribe(self):
        file = self.target_queue.get()
        self.buffer.put(self.stt.transcribe(file))

    def run(self):
        while not self.stop_flag.is_set():
            if not self.target_queue.empty():
                t = time.time()
                stt_stream_logger.info("Transcribing...")
                self.transcribe()
                stt_stream_logger.info(f"Transript completed. Time elapsed: {time.time() - t}")
        
        while not self.target_queue.empty():
            t = time.time()
            stt_stream_logger.info("Transcribing...")
            self.transcribe()
            stt_stream_logger.info(f"Transript completed. Time elapsed: {time.time() - t}")


class STTRecStream:
    rec_stream: RecordingStream
    stt_stream: STTStream
    buffer: Queue
    rec_stop_flag: threading.Event
    stt_stop_flag: threading.Event
    general_stop_flag: threading.Event = threading.Event()

    def __init__(self, **kwargs):
        self.rec_stream = RecordingStream(**kwargs)
        self.stt_stream = STTStream(target_queue=self.rec_stream.get_queue())
        self.buffer = self.stt_stream.get_buffer()

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
            pass

        self.rec_stop_flag.set()
        listening_loop.join()
        self.stt_stop_flag.set()
        transcribing_loop.join()


def test1():
    stream = RecordingStream()
    listening_loop = threading.Thread(target=stream.run, kwargs={"duration": 5})
    stop_flag = stream.stop_flag
    data = stream.file_queue

    print("Strat...")
    listening_loop.start()
    time.sleep(10)
    stop_flag.set()

    listening_loop.join()
    while not data.empty():
        print(data.get())


def test2():
    rec_stream = RecordingStream()
    stt_stream = STTStream(target_queue=rec_stream.get_queue())
    buffer = stt_stream.get_buffer()

    rec_thread = threading.Thread(target=rec_stream.run, kwargs={"duration": 10})
    stt_thread = threading.Thread(target=stt_stream.run)

    rec_flag = rec_stream.get_stop_flag()
    stt_flag = stt_stream.get_stop_flag()

    rec_thread.start()
    stt_thread.start()

    time.sleep(11)
    rec_flag.set()
    stt_flag.set()

    rec_thread.join()
    stt_thread.join()

    while not buffer.empty():
        print(buffer.get())


if __name__ == "__main__":
    test2()
