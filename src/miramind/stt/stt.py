from shared import MyClient, S, msg
from dotenv import load_dotenv
import os


class STT:
    client: any

    def __init__(self):
        self.client = MyClient.get()

    def transcribe(self, file) -> dict[str: str]:
        load_dotenv()
        with open(file, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(model=os.environ.get("STT_DEPLOYMENT", "gpt-4o-transcribe"),
                                                                 file=audio_file,
                                                                 response_format="json",)
            
        messages = [msg(S, "Detect language of the following text. Your answer should be one word. Example: english, polish, german."),
                    msg(S, f"Text: {transcript.text}")]
        response = self.client.chat.completions.create(model=os.environ.get("LANG_DETECT_DEPLOYMENT", "gpt-4o"),
                                                       messages=messages,
                                                       temperature=0.0)
        
        language = response.choices[0].message.content
        return {"language": language,
                "transcript": transcript.text}
        

if __name__ == "__main__":
    load_dotenv()
    my_stt = STT()
    t = my_stt.transcribe(f"{os.environ['TESTS_DIR']}/stt/rick_roll.m4a")
    print(t)
    