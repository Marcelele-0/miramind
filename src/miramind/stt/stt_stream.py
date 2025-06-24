import sounddevice as sd
from dotenv import load_dotenv
from queue import Queue
from stt.stt_class import STT
from stt.consts import DURATION, SAMPLE_RATE

import scipy
import threading
import os
import time
import logging
import uuid
import base64


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

    def __init__(self, save_dir: str = None, logger=None):
        """
        Constructor of RecordingStream class.

        Args:
            save_dir: path to directory where recordings are saved. Default depends on .env file.
            logger: logging instance used for logging.
        """
        self._file_queue = Queue()
        self.save_dir = save_dir if save_dir is not None else f"{os.environ['MIRAMIND_TEMP']}/sttr_temp"
        os.makedirs(self.save_dir, exist_ok=True)
        self._stop_flag = threading.Event()
        self.logger = logger if logger is not None else logging.getLogger()

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
    def record(path: str = "output.wav", logger: logging.Logger = None, **kwargs):
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
        logger = logging.getLogger() if logger is None else logger

        # logger.info("Recording...")
        t = time.time()
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2)
        sd.wait()
        logger.info(f"Recording completed. Time elapsed {time.time() - t}")
        t = time.time()
        scipy.io.wavfile.write(path, sample_rate, audio)
        logger.info(f"Saved to {path}")
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
            prompting_func: function to be called when recording is starting.
            loop_indicator_func: function to indicate change of chunks.
            
            Rest of keyword arguments are specific to prompting_function and loop_indicator_func.

        Returns:
            None
        """

        # first lagged run
        path = f"{self.save_dir}/{get_short_uuid()}.wav"
        self.logger.info("First rec")
        self.record(path=path, logger=self.logger, duration=0.1)
        kwargs.get("prompting_func", lambda **x: print("Start speaking"))(**kwargs)
        loop_index = 0
        t = time.time()

        while not self._stop_flag.is_set():
            path = f"{self.save_dir}/{get_short_uuid()}.wav"
            self.record(path=path, logger=self.logger, **kwargs)
            self._file_queue.put(path)
            loop_index += 1
            kwargs.get("loop_indicator_func", lambda **x: print(f"Loop nr {loop_index}, time {time.time() - t}"))(**kwargs)
            t = time.time()


class STTStream:
    """
    Class for handling transcriptions of recorded files.

    Attributes:
        target_queue: Queue instance containing paths of recordings to transcribe.
        stt: STT instance used to transcribe recordings.
        stop_flag: threading.Event instance used to stop run method.
        buffer: Queue instance where transcripts are put.
    """

    def __init__(self, target_queue, client, logger=None):
        """
        Constructor of STTStream.

        Args:
            target_queue: Queue instance where paths of files to transcribe are stored.
            client: client instance used for API calls.
            logger: logger instance used for logging.
        """
        self.target_queue = target_queue
        self.stt = STT(client)
        self.logger = logger if logger is not None else logging.getLogger()
        self.buffer = Queue()
        self.stop_flag = threading.Event()

    def get_stop_flag(self):
        """
        Get stop_flag attribute.
        """
        return self.stop_flag
    
    def get_buffer(self):
        """
        Get buffer attribute.
        """
        return self.buffer

    def transcribe(self):
        """
        Methods that transcribes first file from _target_queue and puts transcript to _buffer.

        Returns:
            file, transcript: path of transcribed file and transcription
        """
        file = self.target_queue.get()
        transcript = self.stt.transcribe(file)
        self.buffer.put(transcript)
        return file, transcript

    def run(self, verbose=True):
        """
        Method used as target function of a Thread. The using this method will result in transcribing files enqueued in target_queue,
        then transcripts are put into _buffer. It will be stopped when _stop_flag is set.

        Args:
            verbose: bool = True: If True then log transcripts. 

        Returns:
            None
        """
        while not self.stop_flag.is_set():
            if not self.target_queue.empty():
                t = time.time()
                file, transcript = self.transcribe()
                if verbose:
                    try:
                        self.logger.info(f"Transcript of {file} completed. Time elapsed: {time.time() - t}.\n Transcript: {transcript["transcript"]}")
                    except UnicodeEncodeError:
                        self.logger.info(f"Transcript of {file} completed. Time elapsed: {time.time() - t}")
                else:
                    self.logger.info(f"Transcript of {file} completed. Time elapsed: {time.time() - t}")

        while not self.target_queue.empty():
            t = time.time()
            file, transcript = self.transcribe()
            if verbose:
                try:
                    self.logger.info(f"Transcript of {file} completed. Time elapsed: {time.time() - t}.\n Transcript: {transcript["transcript"]}")
                except UnicodeEncodeError:
                    self.logger.info(f"Transcript of {file} completed. Time elapsed: {time.time() - t}")
            else:
                self.logger.info(f"Transcript of {file} completed. Time elapsed: {time.time() - t}")


class RecSTTStream:
    """
    Class used for creating and running recording and transcription in parallel.

    Attributes:
        buffer: Queue instance where transcripts are stored.
        rec_thread: thread responsible for running recording.
        stt_thread: thread responsible for creating transcripts.
        rec_flag: event used to stop rec_thread.
        stt_flag: event used to stop stt_thread.
    """

    def __init__(self, client, duration=DURATION, sample_rate=SAMPLE_RATE, verbose=True):
        """
        Constructor of RecSTTStream.

        Args:
            client: client instance used for API calls.
            duration: duration of a chunk.
            sample_rate: sample rate of a chunk.
            verbose: if True, log verbosity increased.
        """
        rec_stream = RecordingStream()
        stt_stream = STTStream(target_queue=rec_stream.get_file_queue(), client=client)
        self.buffer = stt_stream.get_buffer()

        self.rec_thread = threading.Thread(target=rec_stream.run, kwargs=kwargs, name="RECORDING THREAD")
        stt_thread_kwargs = {"verbose": kwargs.get("verbose", True)}
        self.stt_thread = threading.Thread(target=stt_stream.run, kwargs=stt_thread_kwargs, name="STT THREAD")

        self.rec_flag = rec_stream.get_stop_flag()
        self.stt_flag = stt_stream.get_stop_flag()

    def start(self):
        """
        Start rec_thread and stt_thread.

        Returns:
            None
        """
        self.rec_thread.start()
        self.stt_thread.start()
    
    def stop(self):
        """
        Stop rec_thread and stt_thread.

        Returns:
            buffer
        """
        self.rec_flag.set()
        self.rec_thread.join()
        self.stt_flag.set()
        self.stt_thread.join()
        return self.buffer


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
    t = time.time()
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
    print(time.time() - t)


def test3():
    """
    Example of usage.
    """
    stream = RecSTTStream(duration=3)
    stream.start()
    for i in range(25):
        time.sleep(1)
        print(i + 1)

    stream.stop()
    while not stream.buffer.empty():
        print(stream.buffer.get())


if __name__ == "__main__":
    test3()
