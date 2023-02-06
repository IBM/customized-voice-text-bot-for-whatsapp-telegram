FROM python:3.11-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
EXPOSE 8080

# Choose a bot application (WhatsApp or Telegram) and uncomment its respective line
# CMD ["gunicorn", "-b", ":8080", "whatsapp:app"]   # WhatsApp Bot
# CMD ["python3", "telegram_bot.py"]                # Telegram Bot