from unittest.mock import MagicMock, patch

import pytest

from miramind.audio.stt.stt_class import STT, LinearListeningSTT


def test_STT(mocker):
    # Mocking
    mock_transcript = mocker.Mock()
    mock_transcript.text = "fake transcript"
    mock_azure_openai_client = mocker.Mock()
    mock_azure_openai_client.audio.transcriptions.create = mocker.Mock(return_value=mock_transcript)
    mocker.patch("builtins.open")
    stt = STT(client=mock_azure_openai_client)
    assert stt.transcribe("fake file") == {"transcript": "fake transcript"}


def test_linear_stt(mocker):
    mocker.patch("miramind.audio.stt.stt_class.sd.rec", return_value=None)
    mocker.patch("miramind.audio.stt.stt_class.sd.wait")
    mocker.patch("miramind.audio.stt.stt_class.sf.write")
    mock_transcript = mocker.Mock()
    mock_transcript.text = "fake transcript"
    mock_azure_openai_client = mocker.MagicMock()
    mock_azure_openai_client.audio.transcriptions.create.return_value = mock_transcript

    llstt = LinearListeningSTT(client=mock_azure_openai_client)
    result = llstt.run()
    assert result["transcript"] == "fake transcript"
