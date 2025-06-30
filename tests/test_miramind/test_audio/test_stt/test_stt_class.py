import os
import pathlib

from dotenv import load_dotenv
from pytubefix import YouTube
from shared.utils import get_azure_openai_client
from stt.stt_class import STT
from stt.stt_stream import get_short_uuid


def test_STT():
    assert True
