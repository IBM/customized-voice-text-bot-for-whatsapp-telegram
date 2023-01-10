FROM python:3.11-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
EXPOSE 8080
CMD ["gunicorn", "-b", ":8080", "whatsapp:app"]