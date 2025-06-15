from shared import MyClient
from dotenv import load_dotenv
import os


class STT:
    def __init__(self):
        self.client = MyClient.get()

    def transcribe(self, file):
        load_dotenv()
        with open(file, "rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(model=os.environ.get("STT_MODEL", "gpt-4o-transcribe"),
                                                                    file=audio_file)
            return transcription
        