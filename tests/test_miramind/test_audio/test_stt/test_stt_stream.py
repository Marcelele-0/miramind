import time
from queue import Queue
from dotenv import load_dotenv

from miramind.audio.stt.stt_stream import RecordingStream, RecSTTStream, STTStream


def test_recording(mocker):
    load_dotenv()
    # Mock recording and file write
    mocker.patch("miramind.audio.stt.stt_stream.sd.rec", return_value=[[0]])
    mocker.patch("miramind.audio.stt.stt_stream.sd.wait")
    mocker.patch("miramind.audio.stt.stt_stream.scipy.io.wavfile.write")

    logger = mocker.Mock()
    rec = RecordingStream(logger=logger)

    # Act
    rec.record(path="fake.wav", logger=logger, duration=0.1, sample_rate=16000)

    # Assert
    logger.info.assert_any_call("Saved to fake.wav")


def test_stt(mocker):
    load_dotenv()
    # mocking
    mock_stt = mocker.Mock()
    mock_stt.transcribe = mocker.Mock(return_value={"transcript": "Hello!"})
    mocker.patch("miramind.audio.stt.stt_stream.STT", return_value=mock_stt)

    q = Queue()
    q.put("fake file.wav")
    stt_stream = STTStream(target_queue=q, client="fake client")
    stt_stream.transcribe()

    buffer = stt_stream.get_buffer()
    assert buffer.get() == {"transcript": "Hello!"}


def test_recsttstream(mocker):
    load_dotenv()
    # mocking
    mock_stt = mocker.Mock()
    mock_stt.transcribe = mocker.Mock(return_value={"transcript": "Hello!"})
    mocker.patch("miramind.audio.stt.stt_stream.STT", return_value=mock_stt)
    mocker.patch("miramind.audio.stt.stt_stream.sd.rec", return_value=[[0]])
    mocker.patch("miramind.audio.stt.stt_stream.sd.wait")
    mocker.patch("miramind.audio.stt.stt_stream.scipy.io.wavfile.write")

    recstt_stream = RecSTTStream(client="fake client")
    recstt_stream.start()
    time.sleep(1)
    recstt_stream.stop()
    buffer = recstt_stream.buffer

    assert buffer.qsize() > 0
    while buffer.qsize() > 0:
        transcript = buffer.get()
        assert transcript["transcript"] == "Hello!"
