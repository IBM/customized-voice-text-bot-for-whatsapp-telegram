import hashlib
import json
from datetime import datetime
from flask import Flask, request
from werkzeug.exceptions import HTTPException
from file_management import save_media_file
from audio_services import process_audio_stt
from redirect_request import redirect_request
from twilio_deliver import delivering_answer_whatsapp_twilio

########################
# creating the Flask app
app = Flask(__name__)

@app.errorhandler(HTTPException)
def handle_exception(e):
    """
    This function is used to handle HTTP errors that may result from specific 
    Flask actions. Return JSON instead of HTML for HTTP errors.

    Parameters
    ----------
    e: HTTPException error
        the error
        
    Returns: 
    ----------
        It uses Flask's @app.errorhandler(HTTPException) decorator to handle HTTP errors by converting the error to JSON format instead of HTML and returning it to the user.
    """
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

@app.route("/chatbot-message", methods=['POST'])
def process_msg():
    """
    This function handles the route, which is for receiving POST messages from 
    WhatsApp users through Twilio. It parses each message and passes it to the
    message handler. It also handles returning responses to WhatsApp users, 
    which can be audio or text.

    Returns
    -------
    resp : MessagingResponse
        A Twilio message, can be audio or text. For more information on how to use 
        the class, you can refer to the documentation 
        `https://www.twilio.com/docs/libraries/reference/twilio-python/`
    """

    user_number_ID = request.values.get('WaId')
    encrypted_user_number_ID = hashlib.sha256(
        user_number_ID.encode()).hexdigest()
    timestamp = datetime.now().utcnow().strftime("%d-%m-%Y_%H:%M:%S:%f_UTC")
    non_supported_file = False
    message_is_audio = False

    if 'MediaContentType0' in request.values:
        # If the incoming message is a media file
        if request.values['MediaContentType0'] == 'audio/ogg':
            # If the incoming message is a recorded audio file
            message_is_audio = True
            audio_link, message_recognized = process_audio_stt(
                request.values['MediaUrl0'], 
                encrypted_user_number_ID, 
                timestamp)
            message = [audio_link, message_recognized]
            assistant_answer = redirect_request(
                message, 
                encrypted_user_number_ID, 
                message_is_audio, 
                timestamp,
                non_supported_file)
        else:
            # If the incoming message is a non-supported file
            non_supported_file = True
            file_link = save_media_file(
                encrypted_user_number_ID,
                timestamp,
                request.values['MediaContentType0'],
                request.values['MediaUrl0'])
            assistant_answer = redirect_request(
                file_link,
                encrypted_user_number_ID,
                message_is_audio,
                timestamp,
                non_supported_file)
    else:
        # If the incoming message is a text message
        message = str(request.values.get('Body'))
        message = message.replace('\n', ' ').capitalize()
        assistant_answer = redirect_request(
            message,
            encrypted_user_number_ID,
            message_is_audio,
            timestamp,
            non_supported_file)

    return delivering_answer_whatsapp_twilio(
        assistant_answer, user_number_ID)

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 8080, debug = True)