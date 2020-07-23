FROM python:3.7-slim

MAINTAINER hjrendell@gmail.com

RUN apt-get update && apt-get install -y git
RUN pip install 'pipenv==2018.11.26'

WORKDIR /app

COPY Pipfile Pipfile.lock /app/
RUN pipenv install --system --deploy

COPY . /app

CMD python echo/bot.py -t $TOKEN
