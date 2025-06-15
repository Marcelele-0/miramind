from pytubefix import YouTube
from pytubefix.cli import on_progress
from dotenv import load_dotenv
import logging
import os


logging.basicConfig(level=logging.DEBUG)


def download_yt_audio(url=None, name="test-audio"):
    load_dotenv()
    if url is None:
        url = "https://www.youtube.com/watch?v=ViQ1PWJhcvk&t=543s"

    yt = YouTube(url, on_progress_callback=on_progress)
    yt.title = name
    ys = yt.streams.get_audio_only()
    test_dir = f"{os.environ['TESTS_DIR']}/stt"
    logging.debug(test_dir)
    ys.download(f"{os.environ['TESTS_DIR']}\\stt")


if __name__ == "__main__":
    download_yt_audio()