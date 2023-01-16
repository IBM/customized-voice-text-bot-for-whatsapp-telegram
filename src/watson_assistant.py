import os
from dotenv import load_dotenv
from datetime import datetime
from ibm_watson import AssistantV2, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from audio_services import process_audio_tts
from db import update_conversation_shift, upload_specific_feature

########################
# Setting Environment Variables and setting up services
load_dotenv() # This is used to enable loading environment variables from the
              # .env file
WA_API_KEY            = os.getenv('WA_API_KEY')
WA_ID                 = os.getenv('WA_ID')
WA_SERVICE_URL        = os.getenv('WA_SERVICE_URL')
DEFAULT_ERROR_MESSAGE = str(
    os.getenv('DEFAULT_ERROR_MESSAGE')).replace("_"," ")

# Configuring and authenticating Watson Assistant
assistant = AssistantV2(
    version='2021-11-27',
    authenticator=IAMAuthenticator(WA_API_KEY))
assistant.set_service_url(WA_SERVICE_URL)

# Setting the media response types of Watson Assistant
media_response = ["audio", "video", "image"]

def create_session_ID() -> str:
    """
    Create a new session ID for a user in the Watson Assistant service.

    Returns
    -------
    str
        The session ID.
    """
    try:
        session_ID = assistant.create_session(WA_ID).get_result()["session_id"]
        return session_ID
    except ApiException as ex:
        f"WA Method failed with status code {str(ex.code)} ~ {ex.message}"

def cleaning_text_formatting(text: str) -> str:
    """
    Removes unwanted characters from the text.

    Parameters
    ----------
    text : str
        The text to be cleaned.

    Returns
    -------
    str
        The cleaned text.
    """
    return ((str(text).replace("_", "")).replace("*", "")).replace("\n", " ")

def filtering_answers_to_return(response: list, user_ID: str, session_ID: str, message_is_audio: bool, timestamp: float) -> list:
    """
    Given a list of possible answers from a chatbot, this function filters and formats the answers to return to the user. 
    If the message is audio, the function processes the audio and returns a link to the audio file, along with the original text.
    If the response contains only media responses, the function returns the link to the media.

    Parameters
    ----------
    response : list
        List of possible answers from the chatbot, where each answer is a dictionary with keys "response_type" and "text" or "source".
    user_ID : str
        ID of the user.
    session_ID : str
        ID of the user's session.
    message_is_audio : bool
        Indicates whether the message is audio or text
    timestamp : float
        Timestamp of the message

    Returns
    -------
    list
        List of answers to return to the user, where each answer is a string (the text or link to media).
    """

    if len(response) > 1:
        answers_to_return = []
        all_answers       = []
        for answer in response:
            if answer["response_type"] == "text":
                if message_is_audio:
                    phrase     = cleaning_text_formatting(answer["text"])
                    audio_link = process_audio_tts(user_ID, phrase)
                    all_answers.extend([phrase, audio_link, answer["text"]])
                    answers_to_return.extend([audio_link, answer["text"]])

                else:
                    all_answers.append(answer["text"])
                    answers_to_return.append(answer["text"])

            elif answer["response_type"] in media_response:
                all_answers.append(answer["source"])
                answers_to_return.append(answer["source"])

        update_conversation_shift(
            user_ID, session_ID, 'chatbot', 
            all_answers, timestamp)
            
        return answers_to_return

    elif len(response) == 1:
        if response[0]["response_type"] == "text":
            all_answers       = []
            answers_to_return = []

            if message_is_audio:
                phrase     = cleaning_text_formatting(response[0]["text"])
                audio_link = process_audio_tts(user_ID, phrase)
                all_answers.extend([phrase, audio_link, response[0]["text"]])
                answers_to_return.extend([audio_link, response[0]["text"]])
            else:
                all_answers.append(response[0]["text"])
                answers_to_return.append(response[0]["text"])

            update_conversation_shift(
                user_ID, session_ID, 'chatbot',
                all_answers, timestamp)
            return answers_to_return
        
        elif response[0]["response_type"] in media_response:
            update_conversation_shift(
                user_ID, session_ID, 'chatbot',
                response[0]["source"], timestamp)
            return response[0]["source"]
        else:
            update_conversation_shift(
                user_ID, session_ID, 'chatbot',
                DEFAULT_ERROR_MESSAGE, timestamp)
            return DEFAULT_ERROR_MESSAGE

def assistant_conversation(message: str, user_ID: str, session_ID: str, message_is_audio: bool) -> list:
    """
    This function handles the conversation with the assistant. 
    It sends the message to the assistant and retrieves the output, 
    then filters and formats the answers to return to the user. 
    If the conversation creates or updates context variables, 
    the function updates the context accordingly.

    Parameters
    ----------
    message : str
        The message from the user.
    user_ID : str
        ID of the user.
    session_ID : str
        ID of the user's session.
    message_is_audio : bool
        Indicates whether the message is audio or text

    Returns
    -------
    list
        List of answers to return to the user, where each answer is a string (the text or link to media).
    """
    try:
        conversation = assistant.message(
            WA_ID,
            session_ID,
            input = {
                        'text': message,
                        'options': {
                            'return_context': True
                        }
                    }
        ).get_result()
        timestamp = datetime.now().utcnow().strftime("%d-%m-%Y_%H:%M:%S:%f")

        if 'user_defined' in conversation['context']['skills']['main skill']:
            context_variables = (
                conversation['context']['skills']['main skill']['user_defined'])
            upload_specific_feature(
                str(user_ID), session_ID, context_variables)
        
        response = conversation['output']['generic']
        return filtering_answers_to_return(response, user_ID, 
                                           session_ID, message_is_audio, 
                                           timestamp)
    except ApiException as ex:
        if ex.code == 404:
            new_session_ID = create_session_ID()
            return assistant_conversation(
                message, user_ID, new_session_ID, message_is_audio)
        else:
            f"WA Method failed with status code {str(ex.code)} ~ {ex.message}"