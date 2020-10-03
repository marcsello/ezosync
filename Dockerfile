FROM python:3.8

ADD requirements.txt ezosync/ /ezosync/
WORKDIR /ezosync

RUN apt update && apt install -y libmariadb-dev && pip3 install -r requirements.txt


CMD python3 main.py