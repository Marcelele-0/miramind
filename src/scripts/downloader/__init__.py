from pytubefix import YouTube
from pytubefix.cli import on_progress
from dotenv import load_dotenv
import argparse
import logging
import os


logging.basicConfig(level=logging.INFO)


def download_yt_audio(url, name="test-audio"):
    load_dotenv()

    yt = YouTube(url, on_progress_callback=on_progress)
    yt.title = name
    ys = yt.streams.get_audio_only()
    test_dir = f"{os.environ['TESTS_DIR']}/stt"
    logging.debug(test_dir)
    ys.download(f"{os.environ['TESTS_DIR']}\\stt")


def main():
    parser = argparse.ArgumentParser(description="YT downloader")
    parser.add_argument("-url", help="Source url.", type=str)
    parser.add_argument("-name", help="Output file name.", type=str)
    args = parser.parse_args()

    if not args.name:
        name = "audio"
    else:
        name = args.name

    download_yt_audio(url=args.url, name=name)


if __name__ == "__main__":
    main()
