import io
import logging
import threading
import time
from queue import Queue

import numpy as np
import sounddevice as sd
import soundfile as sf

from miramind.audio.stt.consts import DURATION, SAMPLE_RATE
from miramind.audio.stt.stt_class import STT


class ListeningThread(threading.Thread):
    def __init__(
        self,
        return_queue,
        name=None,
        daemon=None,
        flag=None,
        duration=DURATION,
        sample_rate=SAMPLE_RATE,
        sleep_time=1,
        logger=None,
    ):
        super().__init__(name, daemon=daemon)
        self.return_queue = return_queue
        self.flag = flag if flag is not None else threading.Event()
        self.duration = duration
        self.sample_rate = sample_rate
        self.sleep_time = sleep_time
        self.logger = logger if logger is not None else logging.getLogger()

    def get_flag(self):
        return self.flag

    def get_queue(self):
        return self.return_queue

    def run(self):
        index = 0
        while not self.flag.is_set():
            index += 1
            t = time.time()
            audio = sd.rec(
                int(self.duration * self.sample_rate), samplerate=self.sample_rate, channels=1
            )
            sd.wait(self.sleep_time)
            self.return_queue.put(audio)
            self.logger.info(f"Recording chunk nr {index}, time elapsed {time.time() - t}")


def test1():
    from miramind.shared.utils import get_azure_openai_client

    stt = STT(client=get_azure_openai_client())
    print(f"Start, duration = {DURATION}")
    audio1 = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()
    print("END")
    buffer1 = io.BytesIO()
    buffer1.name = "buffer1.wav"
    sf.write(buffer1, audio1, samplerate=SAMPLE_RATE, format='WAV')
    print(stt.transcribe_bytes(buffer1)["transcript"])
    print(len(audio1))

    print(f"Start, duration = {DURATION}")
    audio2 = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()
    print("END")
    buffer2 = io.BytesIO()
    buffer2.name = "buffer2.wav"
    sf.write(buffer2, audio2, samplerate=SAMPLE_RATE, format='WAV')
    print(stt.transcribe_bytes(buffer2)["transcript"])
    print(len(audio2))

    joint_audio = np.append(audio1, audio2, axis=0)
    print(len(joint_audio))
    buffer = io.BytesIO()
    buffer.name = "audio.wav"
    sf.write(file=buffer, data=joint_audio, samplerate=SAMPLE_RATE, format='WAV')
    buffer.seek(0)
    print(stt.transcribe_bytes(buffer)["transcript"])
    # scipy.io.wavfile.write(path, sample_rate, audio)


def test2():
    from miramind.audio.stt.loggers import get_loggers

    rec_logger, _ = get_loggers()
    queue = Queue()
    lt = ListeningThread(return_queue=queue, daemon=False, logger=rec_logger)
    lt.start()
    time.sleep(10)
    lt.get_flag().set()


if __name__ == "__main__":
    test2()
