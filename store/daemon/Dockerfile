FROM ubuntu

RUN apt update -y && \
    DEBIAN_FRONTEND=noninteractive apt install -y python3 python3-pip tzdata && \
    pip3 install --upgrade pip

WORKDIR /app

ADD requirements.txt .

RUN pip3 install -r requirements.txt

ADD . .

ENTRYPOINT ["python3", "/app/application.py"]