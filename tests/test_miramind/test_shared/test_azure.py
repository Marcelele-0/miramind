import logging
from unittest.mock import MagicMock, mock_open, patch

import pytest

from miramind.shared.azure_utils import (
    download_blob,
    get_blob_service_client,
    read_blob,
    upload_file,
)


@pytest.fixture
def mock_logger():
    return logging.getLogger("test_logger")


@patch("miramind.shared.azure_utils.BlobServiceClient")
@patch(
    "miramind.shared.azure_utils.os.environ",
    {"BLOB_STORAGE_CONNECTION_STRING": "fake_connection_string"},
)
def test_get_blob_service_client_success(mock_blob_service_client, mock_logger):
    mock_blob_service_client.from_connection_string.return_value = "MockClient"
    client = get_blob_service_client(logger=mock_logger)
    assert client == "MockClient"
    mock_blob_service_client.from_connection_string.assert_called_once()


@patch("miramind.shared.azure_utils.os.environ", {})
def test_get_blob_service_client_failure(mock_logger):
    with pytest.raises(KeyError):
        get_blob_service_client(logger=mock_logger)


@patch("builtins.open", new_callable=mock_open, read_data=b"fake data")
@patch("miramind.shared.azure_utils.get_blob_service_client")
def test_upload_file_success(mock_get_client, mock_open_file, mock_logger):
    mock_blob_client = MagicMock()
    mock_blob_service_client = MagicMock()
    mock_blob_service_client.get_blob_client.return_value = mock_blob_client
    mock_get_client.return_value = mock_blob_service_client

    upload_file(
        local_file="fake_file.txt",
        target_blob="fake_blob.txt",
        container="fake_container",
        logger=mock_logger,
    )

    mock_blob_client.upload_blob.assert_called_once()
    mock_blob_service_client.get_blob_client.assert_called_once_with(
        container="fake_container", blob="fake_blob.txt"
    )


@patch("builtins.open", new_callable=mock_open)
@patch("miramind.shared.azure_utils.get_blob_service_client")
def test_upload_file_failure(mock_get_client, mock_open_file, mock_logger):
    mock_blob_client = MagicMock()
    mock_blob_client.upload_blob.side_effect = Exception("Upload failed")
    mock_blob_service_client = MagicMock()
    mock_blob_service_client.get_blob_client.return_value = mock_blob_client
    mock_get_client.return_value = mock_blob_service_client

    with pytest.raises(Exception, match="Upload failed"):
        upload_file(
            local_file="fake_file.txt",
            target_blob="fake_blob.txt",
            container="fake_container",
            logger=mock_logger,
        )


@patch("miramind.shared.azure_utils.get_blob_service_client")
def test_read_blob_success(mock_get_client, mock_logger):
    expected_data = b"blob data"
    mock_blob_client = MagicMock()
    mock_blob_client.download_blob.return_value.readall.return_value = expected_data

    mock_blob_service_client = MagicMock()
    mock_blob_service_client.get_blob_client.return_value = mock_blob_client
    mock_get_client.return_value = mock_blob_service_client

    data = read_blob("fake_blob", "fake_container", logger=mock_logger)
    assert data == expected_data


@patch("miramind.shared.azure_utils.get_blob_service_client")
def test_read_blob_failure(mock_get_client, mock_logger):
    mock_blob_client = MagicMock()
    mock_blob_client.download_blob.side_effect = Exception("Read failed")

    mock_blob_service_client = MagicMock()
    mock_blob_service_client.get_blob_client.return_value = mock_blob_client
    mock_get_client.return_value = mock_blob_service_client

    with pytest.raises(Exception, match="Read failed"):
        read_blob("fake_blob", "fake_container", logger=mock_logger)


@patch("builtins.open", new_callable=mock_open)
@patch("miramind.shared.azure_utils.read_blob")
def test_download_blob_success(mock_read_blob, mock_open_file, mock_logger):
    mock_read_blob.return_value = b"blob content"

    download_blob(
        target_blob="test_blob",
        container="test_container",
        download_path="test_download_path.txt",
        logger=mock_logger,
    )

    mock_open_file().write.assert_called_once_with(b"blob content")
