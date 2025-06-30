import os
import pathlib

from dotenv import load_dotenv
from pytubefix import YouTube
from shared.utils import get_azure_openai_client
from stt.stt_class import STT
from stt.stt_stream import get_short_uuid


def test_STT():
    load_dotenv()
    client = get_azure_openai_client()
    my_stt = STT(client=client)
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley"
    yt = YouTube(url)
    yt.title = get_short_uuid()
    ys = yt.streams.get_audio_only()
    os.makedirs(f"{os.environ['MIRAMIND_TEMP']}/", exist_ok=True)
    ys.download(f"{os.environ['MIRAMIND_TEMP']}/")
    t = my_stt.transcribe(f"{os.environ['MIRAMIND_TEMP']}/{yt.title}.m4a")
    pathlib.Path.unlink(f"{os.environ['MIRAMIND_TEMP']}/{yt.title}.m4a")
    assert "transcript" in t
    assert t["transcript"][: len("We're no strangers to love")] == "We're no strangers to love"
