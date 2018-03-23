FROM python:3.6

LABEL maintainer Christopher Medlin <christopherjmedlin@gmail.com>
ENV LANG C.UTF-8

RUN mkdir /frc-team-update-bot
WORKDIR /frc-team-update-bot
ADD requirements.txt /frc-team-update-bot
RUN pip install -r requirements.txt
ADD . /frc-team-update-bot