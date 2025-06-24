from stt.stt_class import STT
from shared.utils import get_azure_openai_client
from dotenv import load_dotenv
import os


def test_STT():
    load_dotenv()
    client = get_azure_openai_client()
    my_stt = STT(client=client)
    t = my_stt.transcribe(f"{os.environ['TESTS_DIR']}/resources/rick_roll.m4a")
    assert "transcript" in t
    assert t["transcript"][: len("We're no strangers to love")] == "We're no strangers to love"
