# Create the environment for Django project
FROM python:3.11

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./telegram_bot .

CMD ["python", "telegram_bot/telegram_bot.py"]
