import os
from twilio.rest import Client as twilio_client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

########################
# Setting Environment Variables and setting up services
load_dotenv() # This is used to enable loading environment variables from the
              # .env file
TWILIO_ACCOUNT_SID    = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN     = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_SANDBOX_NUMBER = os.getenv('TWILIO_SANDBOX_NUMBER')

# Configuring and authenticating Twilio Client
TWILIO_CLIENT_ACCOUNT = twilio_client(
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def answer_is_media(answer: str) -> bool:
    """
    Check whether the given answer is a media file.

    Parameters
    ----------
    answer : str
        The answer from the chatbot

    Returns
    -------
    bool
        True if the answer is a media file, False otherwise.
    """
    common_media_file_types = ['jpg', 'peg', 'png', 'mp3', 'wav', 'ogg', 'mp4', 'pus', 'aac']
    if type(answer) is str:
        if answer[-3:] in common_media_file_types:
            return True
        else:
            return False
    else:
        return False

def answering_with_twilio(
    user_number_ID: int, is_answer_media: bool, content: str):
    """
    Send a message to a user's WhatsApp number using the Twilio API.

    Parameters
    ----------
    user_number_ID : int
        The phone number of the user in E.164 format.
    is_answer_media : bool
        True if the answer is a media file, False otherwise.
    content : str
        The content of the message (either text or media URL).
    """
    if is_answer_media:
        TWILIO_CLIENT_ACCOUNT.messages.create(
            media_url = content,
            from_ = 'whatsapp:+' + TWILIO_SANDBOX_NUMBER,
            to = 'whatsapp:+' + str(user_number_ID))
    else:
        TWILIO_CLIENT_ACCOUNT.messages.create(
            body = content,
            from_ = 'whatsapp:+' + TWILIO_SANDBOX_NUMBER,
            to = 'whatsapp:+' + str(user_number_ID))

from typing import List, Union

def delivering_answer_whatsapp_twilio(
    assistant_answer: Union[str, List[str]], user_number_ID: int) -> str:
    """
    Deliver the chatbot's answer to the user via WhatsApp using the Twilio API.

    Parameters
    ----------
    assistant_answer : Union[str, List[str]]
        The answer from the chatbot.
    user_number_ID : int
        The phone number of the user in E.164 format.

    Returns
    -------
    str
        A TwiML string containing the chatbot's answer.
    """
    resp = MessagingResponse()
    msg = resp.message()
    if type(assistant_answer) is list:
        if len(assistant_answer) > 1:
            for answer in assistant_answer[0:-1]:
                if answer_is_media(answer):
                    answering_with_twilio(
                        user_number_ID, True, answer)
                else:
                    answering_with_twilio(
                        user_number_ID, False, answer)
            if answer_is_media(assistant_answer[-1]):
                msg.media(assistant_answer[-1])
            else:
                msg.body(assistant_answer[-1])
        else:
            if answer_is_media(assistant_answer[0]):
                msg.media(assistant_answer[0])
            else:
                msg.body(assistant_answer[0])
    else:
        if answer_is_media(assistant_answer):
            msg.media(assistant_answer)
        else:
            msg.body(assistant_answer)
    return str(resp)