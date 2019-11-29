from python:3.7-slim

MAINTAINER hjrendell@gmail.com

RUN apt-get update && apt-get install -y git

COPY . /app
WORKDIR /app

RUN pip install pipenv

RUN pipenv install --system --deploy

CMD python echo/bot.py -t $TOKEN
