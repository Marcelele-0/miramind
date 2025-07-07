import logging
import os

from miramind.shared.utils import S, get_azure_openai_client, msg


def get_language_detection_prompt(text):
    """
    Hardcoded prompt for language detection.
    """

    return [
        msg(
            S,
            "Detect language of the following text. Your answer should be one word. Example: english, polish, german.",
        ),
        msg(S, f"Text: {text}"),
    ]


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

        # TODO: decide if this part is necessary
        # response = self.client.chat.completions.create(model=os.environ.get("LANGUAGE_DETECTION_DEPLOYMENT", "04-mini"),
        #                                                messages=get_language_detection_prompt(transcript.text),)


if __name__ == "__main__":
    stt = STT(client=get_azure_openai_client())
    print(stt.transcribe("C:/Users/Mikołaj/PythonProjects/miramind/test_output_sad.wav"))
