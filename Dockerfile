FROM python:2-stretch
MAINTAINER Wayland Jeong "wjeong@hpe.com"
ADD . /app
WORKDIR "/app"
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
EXPOSE 8080
CMD ["happymeeting.py"]
