FROM python:3-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
EXPOSE 8080

# Choose a bot application (WhatsApp or Telegram) and uncomment its respective line
CMD ["gunicorn", "-b", ":8080", "whatsapp:app"]
# CMD ["python3", "telegram_bot.py"]