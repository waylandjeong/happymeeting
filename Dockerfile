FROM ubuntu:16.04
MAINTAINER Wayland Jeong "wjeong@hpe.com"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
ADD . /app
WORKDIR "/app"
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
EXPOSE 8080
CMD ["happymeeting.py"]
