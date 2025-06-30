from queue import Queue

from miramind.audio.stt.stt_stream import RecordingStream, STTStream


def test_recording(mocker):
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
    # mocking
    mock_stt = mocker.Mock()
    mock_stt.transcribe = mocker.Mock(return_value={"transcript": "Hello!"})
    mocker.patch("miramind.audio.stt.stt_stream.STT", return_value=mock_stt)

    q = Queue()
    q.put("mockfile.wav")
    stt_stream = STTStream(target_queue=q, client="mock_client")
    stt_stream.transcribe()

    buffer = stt_stream.get_buffer()
    assert buffer.get() == {"transcript": "Hello!"}
