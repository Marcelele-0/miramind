import io
import time

import numpy as np
import sounddevice as sd
import soundfile as sf

from miramind.audio.stt.consts import DURATION, SAMPLE_RATE
from miramind.audio.stt.stt_class import STT


class LinearListeningSTT(STT):
    def run(self, chunk_duration=DURATION, sample_rate=SAMPLE_RATE):
        audio = sd.rec(int(chunk_duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()
        buffer = io.BytesIO()
        buffer.name = f"{__name__}.wav"
        sf.write(buffer, audio, samplerate=sample_rate, format='WAV')
        buffer.seek(0)
        return self.transcribe_bytes(buffer)
