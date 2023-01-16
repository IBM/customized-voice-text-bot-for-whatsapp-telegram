import os, requests
from ibm_boto3 import client as COSClient
from ibm_botocore.client import Config
from pathlib import Path
from dotenv import load_dotenv

# Setting Environment Variables and setting up services
load_dotenv()

# Define environment variables
COS_API_KEY_ID = os.getenv('COS_API_KEY_ID')
COS_BUCKET = os.getenv('COS_BUCKET')
COS_BUCKET_LINK = os.getenv('COS_BUCKET_LINK')
COS_ENDPOINT = os.getenv('COS_ENDPOINT')
COS_INSTANCE_CRN = os.getenv('COS_INSTANCE_CRN')

# Create application working directory
DIRECTORY = 'temp'
Path(DIRECTORY).mkdir(parents=True, exist_ok=True)

cos = COSClient(
    service_name='s3',
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version='oauth'),
    endpoint_url=COS_ENDPOINT
)

def write_file(file_path, content):
    """
    Saves the `content` to the file located at `file_path`.

    Parameters
    ----------
    file_path: str
        The path of the file to write
    content: bytes
        The content to write to the file
    """
    with open(file_path, 'wb') as file:
        file.write(content)

def upload_file_cos(file_path):
    """
    Uploads the file located at `file_path` to the COS bucket specified in the environment variables. 
    Deletes the local file after uploading.
    Returns the COS link of the uploaded file.

    Parameters
    ----------
    file_path: str
        The path of the file to upload

    Returns
    -------
    str
        The COS link of the uploaded file
    """
    file_name = file_path.lstrip(DIRECTORY + '/')
    try:
        cos.upload_file(Filename=file_path, Bucket=COS_BUCKET, Key=file_name)
        Path(file_path).unlink(missing_ok=True)
    except Exception as e:
        print(Exception, e)
    else:
        return COS_BUCKET_LINK + '/' + file_name

def save_media_file(user_ID: int, timestamp: str, file_type: str, url: str) -> str:
    """
    Download a media file from a given URL and save it to a user-specific directory.
    
    Parameters
    ----------
    user_ID: int
        Identifier of the user
    timestamp: str
        Timestamp of the file
    file_type: str
        File extension of the media file.
    url: str
        URL of the media file to be downloaded.
        
    Returns
    -------
    str
        The link of the file in cloud object storage
    """
    file = requests.get(url, allow_redirects=True)
    file_path = f"{DIRECTORY}/{user_ID}_{timestamp}_user.{file_type.split('/')[-1]}"
    write_file(file_path, file.content)
    file_link_cos = upload_file_cos(file_path)
    return file_link_cos