import io
import logging
import threading
import time
from queue import Queue

import sounddevice as sd
import soundfile as sf

from miramind.audio.stt.consts import DURATION, SAMPLE_RATE
from miramind.audio.stt.stt_class import STT


class ListeningThread(threading.Thread):
    """
    This thread will put recorded audio in form of numpy array to return queue.
    """

    def __init__(
        self,
        return_queue,
        name=None,
        daemon=None,
        flag=None,
        chunk_duration=DURATION,
        sample_rate=SAMPLE_RATE,
        logger=None,
        prompt=None,
    ):
        """
        Constructor of ListeningThread class.

        Args:
            return_queue: queue.Queue instance, where recorded audio (in form of numpy array) is put.
            name: name of the thread (as per threading.Thread).
            daemon: if True, thread will be daemon.
            flag: threading.Event used to stop this thread (if none is provided one is generated, can be obtained by get_flag method).
            chunk_duration: duration of a chunk.
            sample_rate: recording's sample rate (frames per second).
            logger: logger instance used for logging.
            prompt: function called on beginning of each chunk (if none is provided iw will be print chunk's nuber).

        """
        super().__init__(name=name, daemon=daemon)
        self.return_queue = return_queue
        self.flag = flag if flag is not None else threading.Event()
        self.chunk_duration = chunk_duration
        self.sample_rate = sample_rate
        self.logger = logger if logger is not None else logging.getLogger()
        self.prompt = (
            prompt if prompt is not None else lambda index: print(f"Recording chunk nr {index}")
        )

    def get_flag(self):
        return self.flag

    def get_queue(self):
        return self.return_queue

    def run(self):
        index = 0
        while not self.flag.is_set():
            index += 1
            t = time.time()
            self.prompt(index)
            audio = sd.rec(
                int(self.chunk_duration * self.sample_rate), samplerate=self.sample_rate, channels=1
            )
            sd.wait()
            self.return_queue.put(audio)
            self.logger.info(
                f"{self.name}: recording chunk nr {index}, time elapsed {time.time() - t}"
            )


class TranscribingBytesThread(threading.Thread):
    """
    Thread that transcribes audio saved as numpy array.
    """

    def __init__(
        self,
        target_queue,
        stt,
        name=None,
        flag=None,
        buffer=None,
        logger=None,
        daemon=False,
        sample_rate=SAMPLE_RATE,
    ):
        """
        Constructor of TranscribingBytesThread.

        Args:
            target_queue: queue.Queue instance containing arrays representing sound to transcribe.
            stt: STT instance used for transcribing.
            name: name of the thread.
            flag: threading.Event used to stop this thread (if none is provided one is generated, can be obtained by get_flag method).
            buffer: queue.Queue instance where transcripts will be put (if none is provided one will be created and can be accessed by get_buffer method)
            logger: logger instance for logging.
            daemon: if True this thread will be daemon.
            sample_rate: sample rate of recording (this should match sample rate of recordings)
        """
        super().__init__(
            name=name if name is not None else "Transcribing Bytes Thread", daemon=daemon
        )
        self.target_queue = target_queue
        self.logger = logger if logger is not None else logging.getLogger()
        self.flag = flag if flag is not None else threading.Event()
        self.buffer = buffer if buffer is not None else Queue()
        self.sample_rate = sample_rate
        self.stt = stt

    def get_buffer(self):
        return self.buffer

    def get_flag(self):
        return self.flag

    def get_target_queue(self):
        return self.target_queue

    def run(self):
        index = 0
        while not self.flag.is_set():
            index += 1
            try:
                t = time.time()
                """
                If process hangs, it may be caused by the following line.
                """
                audio_array = self.target_queue.get()
                bytes_buffer = io.BytesIO()
                bytes_buffer.name = f"chunk_nr_{index}.wav"
                sf.write(bytes_buffer, audio_array, samplerate=self.sample_rate, format="WAV")
                transcript_dict = self.stt.transcribe_bytes(bytes_buffer)
                # TODO: decide if this is necessary
                # self.logger.info(f"{self.name}: transcribed chunk nr {index} in {time.time() - t}. Transcript: {transcript_dict['transcript']}")
                self.logger.info(f"{self.name}: transcribed chunk nr {index} in {time.time() - t}.")
                self.buffer.put(transcript_dict)
            except Exception as e:
                self.logger.error(f"Error: {e}")
                raise e


def timed_listen_and_transcribe(
    client, duration=10, chunk_duration=5, lag=2, buffer=None, rec_logger=None, stt_logger=None
):
    """
    This function joins main functionality of ListeningThread and TranscribingBytesThread. It will record speech for fixed time and then transcribe it.
    The main idea is to employ two listening threads (shifted by lag) to cover all incoming voice, as there is delay between chunks.

    Args:
        client: Azure OpenAI client for api calls.
        duration: duration of whole recording.
        chunk_duration: duration of a recorded chunk.
        lag: time between starting second listening thread (note optimal is hardware dependent).
        buffer: queue.Queue instance where transcripts will be put.
        rec_logger: logger instance that will be passed as a logger of listening thread.
        stt_logger: logger instance that will be passed as a logger of transcribing thread.

    Returns:
        buffer with transcripts (in form of {"transcript": "transcript od audio"}). If buffer arg was provided then it will also put those in buffer else it will return new queue.Queue instance..
    """
    queue = Queue()
    my_buffer = buffer if buffer is not None else Queue()
    listening_thread1 = ListeningThread(
        return_queue=queue,
        name="listening thread 1",
        logger=rec_logger,
        chunk_duration=chunk_duration,
    )
    listening_thread2 = ListeningThread(
        return_queue=queue,
        name="listening thread 2",
        logger=rec_logger,
        chunk_duration=chunk_duration,
    )
    transcribing_thread = TranscribingBytesThread(
        target_queue=queue,
        stt=STT(client=client),
        name="transcribing thread",
        buffer=my_buffer,
        logger=stt_logger,
    )
    listening_thread1.start()
    transcribing_thread.start()
    time.sleep(lag)
    listening_thread2.start()
    time.sleep(duration - lag)
    listening_thread1.get_flag().set()
    listening_thread2.get_flag().set()
    listening_thread1.join()
    listening_thread2.join()
    transcribing_thread.get_flag().set()
    transcribing_thread.join()
    return my_buffer


def test2():
    from miramind.audio.stt.loggers import get_loggers
    from miramind.shared.utils import get_azure_openai_client

    rec_logger, _ = get_loggers()
    queue = Queue()
    buffer = Queue()
    lt = ListeningThread(return_queue=queue, daemon=False, logger=rec_logger)
    sttt = TranscribingBytesThread(
        target_queue=queue, stt=STT(client=get_azure_openai_client()), buffer=buffer, logger=_
    )
    lt.start()
    sttt.start()
    time.sleep(10)
    lt.get_flag().set()
    lt.join()
    sttt.get_flag().set()
    sttt.join()
    while not buffer.empty():
        print(buffer.get())


def test3():
    from miramind.audio.stt.loggers import get_loggers
    from miramind.shared.utils import get_azure_openai_client

    rec_l, stt_l = get_loggers()
    buffer = timed_listen_and_transcribe(
        client=get_azure_openai_client(), rec_logger=rec_l, stt_logger=stt_l
    )
    while not buffer.empty():
        print(buffer.get())


if __name__ == "__main__":
    test3()
