import os, requests
from datetime import datetime
from dotenv import load_dotenv
from ibm_watson import SpeechToTextV1, TextToSpeechV1, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from pathlib import Path
from file_management import write_file, upload_file_cos

########################
# Setting Environment Variables and setting up services
load_dotenv() # This is used to enable loading environment variables from the
              # .env file
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

# Setting the application working directory
directory = 'temp'
Path(directory).mkdir(
    parents = True, exist_ok = True)

def tts(file_path, query):
    """
    Given a query as a string, this function will request a speech synthesis 
    from text, download the resulting audio file, which was encoded in mp3, 
    and save the .mp3 file in the file path provided.

    param: file_path, the file path to save the download file.
        type: str

    param: text, the text to convert to speech.
        type: str
    
    returns: file is downloaded to the system.
        type: None
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
    This function requests a speech synthesis to the tts function and upload
    the resulting file to IBM Cloud Object Storage.

    param: user_ID, the user ID to identify the audio file origin on 
    Object Storage
        type: str

    param: query, the text to convert to speech
        type: str
    
    returns: audio file public url on Cloud Object Storage
        type: str
    """
    dt_format       = "%d-%m-%Y_%H:%M:%S:%f_UTC"
    timestamp       = datetime.now().utcnow().strftime(dt_format)
    audio_file_name = (directory
                       + '/' + str(user_ID)
                       + "_" + str(timestamp)
                       + "_chatbot.mp3")
    tts(audio_file_name, query)
    return upload_file_cos(audio_file_name)

def stt(voice):
    """
    This function requests a text transcription of a given .ogg audio file
    to IBM STT API, and returns the transcription as a string. 

    param: voice, the voice audio file content
        type: str
    returns: the speech transcription
        type: str
    """
    try: 
        text_from_speech = speech_to_text.recognize(
            audio        = voice,
            content_type = 'audio/ogg',
            model        = STT_MODEL
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

def process_audio_stt(url, user_ID, timestamp):
    """
    This function downloads an audio file sent from user, uploads it
    to IBM Cloud Object Storage, then delete the local file. After that,
    the audio file content, previously stored in a local var, is sent to
    the stt function.

    param: url, the url from the audio sent by user origin on Object Storage
        type: str

    param: user_ID, the id of the user who sent the audio
        type: int
    
    param: timestamp, the exact moment when user sent the audio
        type: float
    
    returns: audio file public url on Cloud Object Storage and the
    recognized text from the audio.
        type: str, str
    """
    audio_file_directory = directory+'/'+str(user_ID)+'_'+str(timestamp)+'.ogg'
    voice = requests.get(url, allow_redirects=True)
    write_file(audio_file_directory, voice.content)
    audio_link_cos  = upload_file_cos(audio_file_directory)
    text_from_voice = stt(voice.content)
    return audio_link_cos, text_from_voice