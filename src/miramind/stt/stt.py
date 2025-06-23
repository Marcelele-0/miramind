from shared import MyClient, S, msg
from dotenv import load_dotenv
import os


def get_language_detection_prompt(text):
    """
    Hardcoded prompt for language detection.
    """

    return [msg(S, "Detect language of the following text. Your answer should be one word. Example: english, polish, german."),
            msg(S, f"Text: {text}")]


class STT:
    """
    A class handling transcribing audio files.

    Attributes:
        client: client instance used for API calls.
    """

    def __init__(self):
        """
        Constructor of STT class.
        """
        
        self.client = MyClient.get()

    def transcribe(self, file_path: str) -> dict[str: str]:
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

        load_dotenv()
        with open(file_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(model=os.environ.get("STT_DEPLOYMENT", "gpt-4o-transcribe"),
                                                                 file=audio_file,
                                                                 response_format="json",)
            
        response = self.client.chat.completions.create(model=os.environ.get("LANGUAGE_DETECTION_DEPLOYMENT", "04-mini"),
                                                       messages=get_language_detection_prompt(transcript.text),)
        
        return {"language": response.choices[0].message.content,
                "transcript": transcript.text}
        

if __name__ == "__main__":
    my_stt = STT()
    t = my_stt.transcribe(f"{os.environ['TESTS_DIR']}/stt/rick_roll.m4a")
    print(t)
    