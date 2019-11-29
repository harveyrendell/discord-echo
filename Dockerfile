FROM python:3.7-slim

MAINTAINER hjrendell@gmail.com

RUN apt-get update && apt-get install -y git

WORKDIR /app

COPY Pipfile Pipfile.lock /app/
RUN pip install pipenv
RUN pipenv install --system --deploy

COPY . /app

CMD python echo/bot.py -t $TOKEN
