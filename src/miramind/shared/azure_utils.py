import logging
import os

from azure.storage.blob import BlobServiceClient


def get_blob_service_client(logger=None):
    """
    Easy way to get blob service client for API calls.

    Args:
        logger instance for logging.

    Returns:
        blob service client instance
    """
    logger = logger if logger is not None else logging.getLogger()
    try:
        connection_string = os.environ["BLOB_STORAGE_CONNECTION_STRING"]
        return BlobServiceClient.from_connection_string(connection_string)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def upload_file(local_file, target_blob, container, blob_service_client=None, logger=None):
    """
    Upload file to storage acount.

    Args:
        local_file: path of file to upload.
        target_blob: name of blob, that will represent local_file.
        container: container where target blob wil be stored.
        blob_service_client: client instance (connected with appropriate storage account). Must have specified container.
        logger: logger instance for logging.
    """
    logger = logger if logger is not None else logging.getLogger()
    blob_service_client = (
        blob_service_client
        if blob_service_client is not None
        else get_blob_service_client(logger=logger)
    )
    with open(local_file, "rb") as file:
        try:
            blob_client = blob_service_client.get_blob_client(container=container, blob=target_blob)
            blob_client.upload_blob(file)
            logger.info(f"{local_file} uploaded to {target_blob} in {container}.")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise e


def read_blob(target_blob, container, blob_service_client=None, logger=None):
    """
    Get content of a blob stored in Azure.

    Args:
        target_blob: name of blob that will be read.
        container: name of the container with target blob.
        blob_service_client: client used for API calls (default is to get a new client).
        logger: logger instance for logging.

    Returns:
        target blob in bytes form.
    """
    logger = logger if logger is not None else logging.getLogger()
    blob_service_client = (
        blob_service_client
        if blob_service_client is not None
        else get_blob_service_client(logger=logger)
    )
    try:
        blob_client = blob_service_client.get_blob_client(container=container, blob=target_blob)
        downloaded_bytes = blob_client.download_blob().readall()
        logger.info(f"Successfully read {target_blob} from {container}.")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def download_blob(target_blob, container, download_path, blob_service_client=None, logger=None):
    """
    Save result of read_blob to file.

    Args:
        target_blob: name of blob that will be read.
        container: name of the container with target blob.
        download_path: path of saved file.
        blob_service_client: client used for API calls (default is to get a new client).
        logger: logger instance for logging.
    """
    with open(download_path, "wb") as f:
        f.write(
            read_blob(
                target_blob=target_blob,
                container=container,
                blob_service_client=blob_service_client,
                logger=logger,
            )
        )
