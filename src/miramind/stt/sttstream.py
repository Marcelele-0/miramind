import sounddevice as sd
from scipy.io.wavfile import write
from stt import STT
from queue import Queue
from dotenv import load_dotenv
import threading
import os
import time
import logging


logging.basicConfig(level=logging.WARNING)
sttr_stream_logger = logging.getLogger("sttr_stream_logger")
sttr_stream_logger.setLevel(logging.INFO)


class STTRecordingStream:
    data_queue: Queue
    temp_file: str
    stt: STT
    stop_flag: threading.Event = threading.Event()

    def __init__(self, data_queue: Queue = None, temp_file: str = "sttr_temp.wav"):
        load_dotenv()
        self.stt = STT()
        if data_queue is None:
            data_queue = Queue()
        self.data_queue = data_queue
        self.temp_file = f"{os.environ["TEMP"]}/{temp_file}"

    '''
    Some getters.
    '''
    def get_queue(self):
        return self.data_queue
    
    def get_stop_flag(self):
        return self.stop_flag
    
    def read(self):
        return self.data_queue.get()
    
    '''
    Static method used to record to file.
    '''
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
            print("Recording saved to output.wav")

    '''
    Transcribe temp file asociated with stream.
    '''
    def transcribe_recent_input(self):
        return self.stt.transcribe(self.temp_file)
    
    '''
    Listening loop.
    '''
    def run(self, **settings):
        while not self.stop_flag.is_set():
            t = time.time()
            sttr_stream_logger.info("Recording...")
            self.record(path=self.temp_file, settings=settings)
            # self.data_queue.put("recording")
            sttr_stream_logger.info(f"Recording done in {time.time() - t}. Transcribing...")
            t = time.time()
            transcript = self.transcribe_recent_input()
            self.data_queue.put(transcript)
            sttr_stream_logger.info(f"Transcribing done in {time.time() - t}")


if __name__ == "__main__":
    stream = STTRecordingStream()
    listening_loop = threading.Thread(target=stream.run)
    stop_flag = stream.stop_flag
    data = stream.data_queue

    print("Strat...")
    listening_loop.start()
    time.sleep(10)
    stop_flag.set()

    while not data.empty():
        print(data.get())

