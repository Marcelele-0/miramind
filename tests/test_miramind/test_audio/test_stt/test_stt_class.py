from miramind.audio.stt.stt_class import STT


def test_STT(mocker):
    # Mocking
    mock_transcript = mocker.Mock()
    mock_transcript.text = "fake transcript"
    mock_azure_openai_client = mocker.Mock()
    mock_azure_openai_client.audio.transcriptions.create = mocker.Mock(return_value=mock_transcript)
    mocker.patch("builtins.open")
    stt = STT(client=mock_azure_openai_client)
    assert stt.transcribe("fake file") == {"transcript": "fake transcript"}
