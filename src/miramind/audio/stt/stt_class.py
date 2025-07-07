import io
import logging
import os

import sounddevice as sd
import soundfile as sf

from miramind.audio.stt.consts import DURATION, SAMPLE_RATE


class STT:
    """
    A class handling transcribing audio files.

    Attributes:
        client: client instance used for API calls.
    """

    def __init__(self, client, logger=None):
        """
        Constructor of STT class.

        Args:
            client: client instance for API calls.
            logger: logger instance for logging.
        """
        self.client = client
        self.logger = logger if logger is not None else logging.getLogger()

    def transcribe_bytes(self, bytes):
        """
        Transcribe bytes object.

        Args:
            bytes: bytes object representing sound to transcribe.

        Returns:
            dict[str: str]: dict containing transcript (with key "transcript")
        """
        transcript = self.client.audio.transcriptions.create(
            model=os.environ.get("STT_DEPLOYMENT", "gpt-4o-transcribe"),
            file=bytes,
            response_format="json",
        )
        self.logger.info(f"Transcript: {transcript.text}")
        return {"transcript": transcript.text}

    def transcribe(self, file_path: str) -> dict[str:str]:
        """
        Transcribes an audio file and detects the language of the transcript.

        Args:
            file_path (str): Path to the audio file to be transcribed.

        Returns:
            dict[str, str]: A dictionary containing the detected language and the transcribed text.
                            Keys are:
                                - 'language': The detected language (e.g., 'english', 'german').
                                - 'transcript': The transcribed text from the audio.
        """

        with open(file_path, "rb") as audio_file:
            return self.transcribe_bytes(audio_file)


class LinearListeningSTT(STT):
    """
    Linear speech to text class. Subclass of STT. Main use case is calling run method.
    """

    def run(self, chunk_duration=DURATION, sample_rate=SAMPLE_RATE):
        """
        Main functionality of LinearListeningSTT.

        Args:
            chunk_duration: duration (in seconds) of listening before transcribing recorded sound (default 5s).
            sample_rate: recording's sample rate (default 44100).
        """
        audio = sd.rec(int(chunk_duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()
        buffer = io.BytesIO()
        buffer.name = f"{__name__}.wav"
        sf.write(buffer, audio, samplerate=sample_rate, format='WAV')
        buffer.seek(0)
        return self.transcribe_bytes(buffer)
