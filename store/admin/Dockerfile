FROM ubuntu

RUN apt update -y && \
    apt install -y python3 python3-pip && \
    pip3 install --upgrade pip \

WORKDIR /app

EXPOSE 80

ADD requirements.txt .

RUN pip3 install -r requirements.txt

ADD . .

ENTRYPOINT ["python3", "/app/application.py"]
