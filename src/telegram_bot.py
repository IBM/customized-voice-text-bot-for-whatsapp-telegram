import os, requests
from dotenv import load_dotenv
from telegram.ext import *
import telegram
import hashlib
from datetime import datetime
from audio_services import process_audio_stt
from redirect_request import redirect_request

load_dotenv('./venv/master.env')
PORT                 = os.getenv('PORT')
TELEGRAM_BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL') # var must finish with /

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

def answer_is_media(answer):
    common_media_file_types = ['jpg', 'peg', 'png', 'mp3', 'wav', 'ogg', 'mp4', 'pus']
    if type(answer) is str:
        if answer[-3:] in common_media_file_types:
            return True
        else:
            return False
    else:
        return False

def is_photo(text):
    if text[-3:] in ['jpg', 'peg', 'png']:
        return True
    else:
        return False

def is_audio(text):
    if text[-3:] in ['mp3', 'wav', 'ogg', 'mp4', 'pus']:
        return True
    else:
        return False

def change_text_formatting(sentence):
    formatting_replacements = [
        ('[', '\['), (']', '\]'), ('(', '\('), (')', '\)'), ('~', '\~'), \
        ('`', '\`'), ('>', '\>'), ('#', '\#'), ('+', '\+'), ('-', '\-'), \
        ('=', '\='), ('|', '\|'), ('{', '\{'), ('}', '\}'), ('.', '\.'), \
        ('!', '\!')
        ]
    for char, replacement in formatting_replacements:
        if char in sentence:
            sentence = sentence.replace(char, replacement)
    return sentence

def start_command(update, context):
    user_ID = str(update.message.chat_id)
    encrypted_user_ID = hashlib.sha256(user_ID.encode()).hexdigest()
    timestamp = datetime.now().utcnow().strftime("%d-%m-%Y_%H:%M:%S:%f_UTC")
    non_supported_file = False
    message_is_audio = False

    message = 'break'
    assistant_answer = redirect_request(
        message, 
        encrypted_user_ID, 
        message_is_audio, 
        timestamp, 
        non_supported_file)
    return_answer(user_ID, assistant_answer)

def help_command(update, context):
    update.message.reply_text('How can I help you? Please type or say your needs.')

def send_media(user_ID, media):
    if is_photo(media):
        bot.send_photo(user_ID, media)
    elif is_audio(media):
        bot.send_audio(user_ID, media, caption='', title='')
    else:
        bot.send_message(user_ID, media)

def return_answer(user_ID, assistant_answer):
    if type(assistant_answer) is list:
        for answer in assistant_answer:
            if not answer_is_media(answer):
                answer = change_text_formatting(answer)
                bot.send_message(
                    user_ID, answer, parse_mode="MarkdownV2")
            else:
                send_media(user_ID, answer)
    else:
        if not answer_is_media(assistant_answer):
            assistant_answer = change_text_formatting(assistant_answer)
            bot.send_message(
                user_ID, assistant_answer, parse_mode="MarkdownV2")
        else:
            send_media(user_ID, assistant_answer)

def handle_message(update, context):
    user_ID = str(update.message.chat_id)
    encrypted_user_ID = hashlib.sha256(user_ID.encode()).hexdigest()
    timestamp = datetime.now().utcnow().strftime("%d-%m-%Y_%H:%M:%S:%f_UTC")
    non_supported_file = False
    message_is_audio = False

    message = str(update.message.text).capitalize()
    assistant_answer = redirect_request(
        message, encrypted_user_ID, message_is_audio, 
        timestamp, non_supported_file)
    return_answer(user_ID, assistant_answer)

from file_management import save_media_file

def handle_photo(update, context):
    user_ID = str(update.message.chat_id)
    encrypted_user_ID = hashlib.sha256(user_ID.encode()).hexdigest()
    timestamp = datetime.now().utcnow().strftime("%d-%m-%Y_%H:%M:%S:%f_UTC")
    file_type = 'jpg'
    url = update.message.photo[-1].get_file()['file_path']
    non_supported_file = True
    message_is_audio = False

    file_link = save_media_file(encrypted_user_ID, timestamp, file_type, url)
    assistant_answer = redirect_request(
                file_link, encrypted_user_ID, message_is_audio, timestamp, non_supported_file)
    return_answer(user_ID, assistant_answer)    

def handle_voice(update, context):
    user_ID = str(update.message.chat_id)
    encrypted_user_ID = hashlib.sha256(user_ID.encode()).hexdigest()
    timestamp = datetime.now().utcnow().strftime("%d-%m-%Y_%H:%M:%S:%f_UTC")
    non_supported_file = False
    message_is_audio = True

    voice_link = update.message.effective_attachment.get_file()['file_path']
    audio_link, message_recognized = process_audio_stt(
        voice_link, encrypted_user_ID, timestamp)
    message = [audio_link, message_recognized]
    assistant_answer = redirect_request(
        message, encrypted_user_ID, message_is_audio, 
        timestamp, non_supported_file)
    return_answer(user_ID, assistant_answer)
        
def error(update, context):
    print(f"Update {update} caused error {context.error}")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    dp.add_handler(MessageHandler(Filters.voice, handle_voice))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_error_handler(error)

    updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get('PORT', PORT)),
        url_path=TELEGRAM_BOT_TOKEN,
        key='private.key',
        webhook_url=TELEGRAM_WEBHOOK_URL + TELEGRAM_BOT_TOKEN
        )
    updater.idle()

if __name__ == '__main__':
    main()