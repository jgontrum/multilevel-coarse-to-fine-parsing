FROM python:3.6
MAINTAINER Johannes Gontrum <gontrum@me.com>

RUN pip install virtualenv

COPY . /app
RUN cd /app && make clean && make

ENTRYPOINT ["bash", "-c" , "cd /app && env/bin/ctfparser"]
