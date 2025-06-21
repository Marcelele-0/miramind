import sounddevice as sd
from scipy.io.wavfile import write
from .stt import STT
from queue import Queue
from .loggers import stt_stream_logger, rec_stream_logger, SentinelLogger
from dotenv import load_dotenv
import threading
import os
import time
import logging
import uuid
import base64


SENTINEL_LOGGER = SentinelLogger()
DURATION = 5
SAMPLE_RATE = 44100


def get_short_uuid():
    """
    Unique id generator.

    Returns:
        id that is unlikely to have been generated before (str).
    """

    u = uuid.uuid4()
    return base64.urlsafe_b64encode(u.bytes).rstrip(b'=').decode('ascii')


class RecordingStream:
    """
    Class for handling recording speech.

    Attributes:
        _file_queue: Queue instance containing paths to saved files.
        save_dir: path to directory where recordings are saved.
        _stop_flag: threading.Event instance used to stop run method.
    """

    def __init__(self, save_dir: str = None):
        """
        Constructor of RecordingStream class.

        Args:
            save_dir: path to directory where recordings are saved. Default depends on .env file.
        """

        load_dotenv()
        self._file_queue = Queue()
        self.save_dir = save_dir if save_dir is not None else f"{os.environ['MIRAMIND_TEMP']}/{save_dir}"
        self._stop_flag = threading.Event()

    def get_file_queue(self):
        """
        Get _file_queue attribute.
        """

        return self._file_queue
    
    def get_stop_flag(self):
        """
        Get _stop_flag attribute.
        """

        return self._stop_flag

    @staticmethod
    def record(path: str = "output.wav", logger: logging.Logger = SENTINEL_LOGGER, **kwargs):
        """
        Static method used for recording audio. After running this method program will record from default system microphone.

        Args:
            path: path where recording will be saved recording.
            logger: object used for logging purposes.

        Keyword Args:
            duration: duration of recording in seconds.
            sample_rate: sample rate of recording.

        Returns:
            None
        """

        duration = kwargs.get("duration", DURATION)
        sample_rate = kwargs.get("sample_rate", SAMPLE_RATE)

        logger.info("Recording...")
        t = time.time()
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2)
        sd.wait()
        logger.info(f"Recording completed. Time elapsed {time.time() - t}")
        logger.info("Saving...")
        t = time.time()
        write(path, sample_rate, audio)
        logger.info(f"Saving completed. Time elapsed: {time.time() - t}")
    
    def run(self, **kwargs):
        """
        Method used as target function of a Thread. It will record speech in chunks and save recordings to save_dir.
        Result of running this method is twofold:
        - having recordings in a specified directory,
        - having put path of said recordings to file_queue

        Keyword Args:
            duration: duration of recording in seconds.
            sample_rate: sample rate of recording.

        Returns:
            None
        """

        while not self._stop_flag.is_set():
            path = f"{self.save_dir}/{get_short_uuid()}.wav"
            self.record(path=path, logger=rec_stream_logger, **kwargs)
            self._file_queue.put(path)


class STTStream:
    """
    Class for handling transcriptions of recorded files.

    Attributes:
        target_queue: Queue instance containing paths of recordings to transcribe.
        _stt: STT instance used to transcribe recordings.
        _stop_flag: threading.Event instance used to stop run method.
        _buffer: Queue instance where transcripts are put.
    """

    def __init__(self, target_queue):
        """
        Constructor of STTStream.

        Args:
            target_queue: Queue instance where paths of files to transcribe are stored.
        """
        self.target_queue = target_queue
        self._stt = STT()
        self._buffer = Queue()
        self._stop_flag = threading.Event()

    def get_stop_flag(self):
        """
        Get _stop_flag attribute.
        """

        return self._stop_flag
    
    def get_buffer(self):
        """
        Get _buffer attribute.
        """

        return self._buffer

    def transcribe(self):
        """
        Methods that transcribes first file from _target_queue and puts transcript to _buffer.

        Returns:
            None
        """
        file = self.target_queue.get()
        self._buffer.put(self._stt.transcribe(file))

    def run(self):
        """
        Method used as target function of a Thread. The using this method will result in transcribing files enqueued in target_queue,
        then transcripts are put into _buffer. It will be stopped when _stop_flag is set.

        Returns:
            None
        """
        while not self._stop_flag.is_set():
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


def test1():
    stream = RecordingStream()
    listening_loop = threading.Thread(target=stream.run, kwargs={"duration": 5})
    stop_flag = stream._stop_flag
    data = stream._file_queue

    print("Strat...")
    listening_loop.start()
    time.sleep(10)
    stop_flag.set()

    listening_loop.join()
    while not data.empty():
        print(data.get())


def test2():
    rec_stream = RecordingStream()
    stt_stream = STTStream(target_queue=rec_stream.get_file_queue())
    buffer = stt_stream.get_buffer()

    rec_thread = threading.Thread(target=rec_stream.run, kwargs={"duration": 4})
    stt_thread = threading.Thread(target=stt_stream.run)

    rec_flag = rec_stream.get_stop_flag()
    stt_flag = stt_stream.get_stop_flag()

    rec_thread.start()
    stt_thread.start()

    time.sleep(10)
    rec_flag.set()
    stt_flag.set()

    rec_thread.join()
    stt_thread.join()

    while not buffer.empty():
        print(buffer.get())


if __name__ == "__main__":
    test2()
