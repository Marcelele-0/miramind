import os

from azure.storage.blob import BlobServiceClient


def get_blob_service_client():
    connection_string = os.environ["BLOB_STORAGE_CONNECTION_STRING"]
    return BlobServiceClient.from_connection_string(connection_string)


def upload_file(local_file, target_blob, container, blob_service_client=None):
    if blob_service_client is None:
        blob_service_client = get_blob_service_client()
    with open(local_file, "rb") as file:
        blob_client = blob_service_client.get_blob_client(container=container, blob=target_blob)
        blob_client.upload_blob(file)


def download_file(target_blob, container, local_path, blob_service_client=None):
    if blob_service_client is None:
        blob_service_client = get_blob_service_client()
    with open(local_path, "wb") as file:
        blob_client = blob_service_client.get_blob_client(container=container, blob=target_blob)
        file.write(blob_client.download_blob())
