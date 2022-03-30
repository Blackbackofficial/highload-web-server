FROM ubuntu:20.04
MAINTAINER Ivan Chernov (Blackbackofficial)

ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get -y update && apt-get -y upgrade && apt-get -y install python3-pip
RUN pip3 install configparser
RUN pip3 install pathlib
RUN pip3 install urllib3

ADD ./ $WORK/

EXPOSE 80

WORKDIR $WORK/

CMD python3 -u ./main.py