import os
from dotenv import load_dotenv
from typing import List, Union
from watson_assistant import assistant_conversation, create_session_ID
from db import (create_new_document, update_conversation_shift,
                verify_document_exists, viewing_last_session_ID)

########################
# Setting Environment Variable
load_dotenv() # This is used to enable loading environment variables from the
              # .env file
DEFAULT_ERROR_MESSAGE = str(os.getenv('DEFAULT_ERROR_MESSAGE')).replace("_"," ")

session_IDs = {}

def update_session_ID(user_ID: int):
    """
    Create a new session ID and update the user's session ID.
    Also create new documents in the IBM Cloudant database.

    Parameters
    ----------
    user_ID : int
        The ID of the user.
    """
    session_ID = create_session_ID()
    session_IDs[user_ID] = session_ID
    create_new_document(str(user_ID), session_ID)


def checking_user_existence_DB(user_ID: int):
    """
    Check if the user exists in the IBM Cloudant database,
    and update session ID accordingly.

    Parameters
    ----------
    user_ID : int
        The ID of the user.
    """
    if verify_document_exists(user_ID):
        session_IDs[user_ID] = viewing_last_session_ID(user_ID)
    else:
        update_session_ID(user_ID)


def redirect_request(
    message: Union[str, List[str]], user_ID: int, message_is_audio: bool, 
    timestamp: float, non_supported_file: bool) -> str:
    """
    Redirect the user's request to the appropriate function.

    Parameters
    ----------
    message : str
        The message from the user.
    user_ID : int
        The ID of the user.
    message_is_audio : bool
        True if the message is in audio format, otherwise False.
    timestamp : float
        The timestamp of the message.
    non_supported_file : bool
        True if the file type of the message is not supported, otherwise False.

    Returns
    -------
    str
        The response from the chatbot.
    """
    if str(message).lower() == "break":
        update_session_ID(user_ID)
        message = "Hi"
    else:
        checking_user_existence_DB(user_ID)
    update_conversation_shift(
        user_ID, session_IDs[user_ID], 'user', message, timestamp)
    if message_is_audio:
        return assistant_conversation(
            message[1], user_ID, session_IDs[user_ID], message_is_audio)
    elif not non_supported_file:
        return assistant_conversation(
            message, user_ID, session_IDs[user_ID], message_is_audio)
    else:
        update_conversation_shift(
            user_ID, session_IDs[user_ID], 'chatbot',
            DEFAULT_ERROR_MESSAGE, timestamp)
        return DEFAULT_ERROR_MESSAGE