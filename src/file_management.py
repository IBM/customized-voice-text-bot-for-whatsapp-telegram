import os, requests
from ibm_boto3 import client as COSClient
from ibm_botocore.client import Config
from pathlib import Path
from dotenv import load_dotenv

########################
# Setting Environment Variables and setting up services
load_dotenv() # This is used to enable loading environment variables from the
              # .env file
COS_API_KEY_ID   = os.getenv('COS_API_KEY_ID')
COS_BUCKET       = os.getenv('COS_BUCKET')
COS_BUCKET_LINK  = os.getenv('COS_BUCKET_LINK')
COS_ENDPOINT     = os.getenv('COS_ENDPOINT')
COS_INSTANCE_CRN = os.getenv('COS_INSTANCE_CRN')

directory = 'temp'
Path(directory).mkdir(parents=True, exist_ok=True)

cos = COSClient(service_name            = 's3',
                ibm_api_key_id          = COS_API_KEY_ID,
                ibm_service_instance_id = COS_INSTANCE_CRN,
                config                  = Config(signature_version = 'oauth'),
                endpoint_url            = COS_ENDPOINT)

def write_file(file_path, content):
    with open(file_path, 'wb') as file:
        file.write(content)

def upload_file_cos(file_path):
    file_name = file_path.lstrip(directory+'/')
    try:
        cos.upload_file(Filename = file_path,
                        Bucket   = COS_BUCKET,
                        Key      = file_name)
        Path(file_path).unlink(missing_ok = True)
    except Exception as e:
        print(Exception, e)
    else:
        return COS_BUCKET_LINK + '/' + file_name

def save_media_file(user_ID, timestamp, file_type, url):
    file = requests.get(url, allow_redirects=True)
    audio_file_directory = (directory + '/' + str(user_ID) + '_' 
                            + str(timestamp) + '_user.' 
                            + str(file_type[file_type.rfind('/')+1:]))
    write_file(audio_file_directory, file.content)
    file_link_cos = upload_file_cos(audio_file_directory)
    return file_link_cos