from azure.storage.blob import BlobServiceClient
from datetime import datetime

def upload_file (file) -> str:
    AZURE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=inventmais;AccountKey=k7aXP5q5q39y/iSnpVdWYfVvzCKz/kXepvP3+95+oz1aBVKpKj17kdOMZb4ro7M5VaTLOIiSb/rb+AStzZHUsQ==;EndpointSuffix=core.windows.net"
    CONTAINER_NAME = "arquivos"
    LINK_AZURE = "https://inventmais.blob.core.windows.net/"

    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

    if file.filename == '':
        return ""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    file.filename = f"{timestamp}_{file.filename}"

    # Upload para o Azure Blob Storage
    try:
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file.filename)

        blob_client.upload_blob(file, overwrite=True)
        
        return f"{LINK_AZURE}{CONTAINER_NAME}/{file.filename}"
    except:
        return ""