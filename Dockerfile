FROM python:3.8

ENV TZ Europe/Budapest
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ADD requirements.txt ezosync/ /ezosync/
WORKDIR /ezosync

RUN apt update && apt install -y libmariadb-dev && pip3 install -r requirements.txt


CMD python3 main.py