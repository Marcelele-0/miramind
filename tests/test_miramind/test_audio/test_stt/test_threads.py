import threading
import time
from queue import Queue
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from miramind.audio.stt.consts import DURATION, SAMPLE_RATE
from miramind.audio.stt.stt_threads import (
    ListeningThread,
    TranscribingBytesThread,
    timed_listen_and_transcribe,
)


@pytest.fixture
def dummy_audio():
    return np.zeros((int(DURATION * SAMPLE_RATE), 1))


@patch("miramind.audio.stt.stt_threads.sd.rec")
@patch("miramind.audio.stt.stt_threads.sd.wait")
def test_listening_thread_records_and_puts_audio(mock_wait, mock_rec, dummy_audio):
    mock_rec.return_value = dummy_audio
    return_queue = Queue()
    flag = threading.Event()

    thread = ListeningThread(return_queue=return_queue, flag=flag, chunk_duration=DURATION)
    thread.start()
    time.sleep(1)  # allow it to record at least once
    flag.set()
    thread.join()

    assert not return_queue.empty()
    recorded = return_queue.get()
    assert recorded.shape == dummy_audio.shape


@patch("miramind.audio.stt.stt_threads.sf.write")
def test_transcribing_thread_transcribes_audio(mock_sf_write, dummy_audio):
    queue = Queue()
    queue.put(dummy_audio)

    mock_stt = MagicMock()
    mock_stt.transcribe_bytes.return_value = {"transcript": "test transcript"}

    buffer = Queue()
    flag = threading.Event()
    thread = TranscribingBytesThread(
        target_queue=queue,
        stt=mock_stt,
        buffer=buffer,
        flag=flag,
        sample_rate=SAMPLE_RATE,
        timeout=1,
    )
    thread.start()
    time.sleep(1)  # allow time to transcribe
    flag.set()
    thread.join()

    assert not buffer.empty()
    result = buffer.get()
    assert result["transcript"] == "test transcript"


@patch("miramind.audio.stt.stt_threads.sd.rec")
@patch("miramind.audio.stt.stt_threads.sd.wait")
@patch("miramind.audio.stt.stt_threads.sf.write")
@patch("miramind.audio.stt.stt_threads.STT")
def test_timed_listen_and_transcribe(
    mock_stt_class, mock_sf_write, mock_wait, mock_rec, dummy_audio
):
    mock_rec.return_value = dummy_audio

    mock_stt = MagicMock()
    mock_stt.transcribe_bytes.return_value = {"transcript": "chunk"}
    mock_stt_class.return_value = mock_stt

    buffer = timed_listen_and_transcribe(
        client="fake_client", duration=3, chunk_duration=1, lag=1, timeout=1
    )

    transcripts = []
    while not buffer.empty():
        transcripts.append(buffer.get()["transcript"])

    assert len(transcripts) > 0
    assert all(t == "chunk" for t in transcripts)
