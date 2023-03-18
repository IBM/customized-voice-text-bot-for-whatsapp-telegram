import os, requests
from datetime import datetime
from dotenv import load_dotenv
from ibm_watson import SpeechToTextV1, TextToSpeechV1, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from pathlib import Path
from file_management import write_file, upload_file_cos
from typing import Tuple

# Load environment variables
load_dotenv()

# Define environment variables
STT_API_KEY       = os.getenv('STT_API_KEY')
STT_SERVICE_URL   = os.getenv('STT_SERVICE_URL')
STT_MODEL         = os.getenv('STT_MODEL')
TTS_API_KEY       = os.getenv('TTS_API_KEY')
TTS_DEFAULT_VOICE = os.getenv('TTS_DEFAULT_VOICE')
TTS_SERVICE_URL   = os.getenv('TTS_SERVICE_URL')

# Configuring and authenticating STT and TTS
speech_to_text = SpeechToTextV1(IAMAuthenticator(STT_API_KEY))
speech_to_text.set_service_url(STT_SERVICE_URL)
text_to_speech = TextToSpeechV1(IAMAuthenticator(TTS_API_KEY))
text_to_speech.set_service_url(TTS_SERVICE_URL)

# Create application working directory
DIRECTORY = './temp'
Path(DIRECTORY).mkdir(parents=True, exist_ok=True)

def text_to_speech_synthesize(file_path: str, query: str) -> None:
    """
    Given a query as a string, this function will request a speech synthesis 
    from text, download the resulting audio file, which was encoded in mp3, 
    and save the .mp3 file in the file path provided.
    
    Parameters
    ----------
    file_path : str
        The file path to save the download file.
    query : str
        The text to convert to speech.
    
    Returns
    -------
    None
        The function saves the file on the specified path and returns nothing
    
    Raises
    ------
    ApiException
        If the API request fails, it raises an exception with the status code 
        and message provided by the API
    """
    try:
        with open(file_path, 'wb') as audio_file:
            audio_file.write(
                text_to_speech.synthesize(
                    query,
                    voice = TTS_DEFAULT_VOICE,
                    accept = 'audio/mp3'
                ).get_result().content
                )
    except ApiException as ex:
        return "Method failed with status code "+str(ex.code)+": "+ex.message


def process_audio_tts(user_ID, query):
    """
    Requests a text-to-speech synthesis from IBM Watson Text to Speech API
    through the `tts` function, creates a file name based on the user ID,
    timestamp and the string 'chatbot' and saves it to the specified directory,
    then uploads the resulting file to IBM Cloud Object Storage and returns 
    the public URL of the audio file on Cloud Object Storage.
    
    Parameters
    ----------
    user_ID : str
        The user ID used to identify the origin of the audio file on Object Storage
    query : str
        The text to convert to speech
    
    Returns
    -------
    Optional[str]
        The public URL of the audio file on Cloud Object Storage,
        returns None if the uploading fail.
    """
    dt_format       = "%d-%m-%Y_%H:%M:%S:%f_UTC"
    timestamp       = datetime.now().utcnow().strftime(dt_format)
    audio_file_name = (DIRECTORY
                       + '/' + str(user_ID)
                       + "_" + str(timestamp)
                       + "_chatbot.mp3")
    text_to_speech_synthesize(audio_file_name, query)
    return upload_file_cos(audio_file_name)

def speech_to_text_recognize(voice: bytes) -> str:
    """
    Given an audio file in ogg format, this function uses IBM Watson Speech to Text 
    API to transcribe the audio to text.

    Parameters
    ----------
    voice : bytes
        The audio file content, as bytes

    Returns
    -------
    str
        The transcription of the speech, as a string

    Raises
    ------
    ApiException
        If the API request fails, it raises an exception with the status code 
        and message provided by the API
    """
    try: 
        text_from_speech = speech_to_text.recognize(
            audio        = voice,
            content_type = 'audio/ogg',
            model        = STT_MODEL,
            low_latency  = True # Ensure that your model is compatible with Low Latency
        ).get_result()
        if len(text_from_speech['results']) > 0:
            transcript = str(
                text_from_speech['results'][0]['alternatives'][0]['transcript'])
            return transcript.strip().capitalize()
        else:
            return "Message unrecognizable"
    except ApiException as ex:
        print("Method failed with status code "+str(ex.code)+": "+ex.message)
        return "Message unrecognizable"


def process_audio_stt(url: str, user_ID: str, timestamp: str) -> Tuple[str, str]:
    """
    This function downloads an audio file sent from user, uploads it
    to IBM Cloud Object Storage, then delete the local file. After that,
    the audio file content, previously stored in a local var, is sent to
    the "speech_to_text_recognize" function.

    Parameters
    ----------
    url : str
        The url of the audio file on IBM Cloud Object Storage.
    user_ID : str
        The id of the user who sent the audio.
    timestamp : str
        The exact moment when user sent the audio.

    Returns
    -------
    Tuple[str, str]
        A tuple containing the public url of the audio file on IBM Cloud Object Storage 
        and the transcription of the audio file.

    """
    audio_file_directory = f"{DIRECTORY}/{str(user_ID)}_{str(timestamp)}.ogg"
    voice = requests.get(url, allow_redirects=True)
    write_file(audio_file_directory, voice.content)
    audio_link_cos  = upload_file_cos(audio_file_directory)
    text_from_voice = speech_to_text_recognize(voice.content)
    return audio_link_cos, text_from_voice