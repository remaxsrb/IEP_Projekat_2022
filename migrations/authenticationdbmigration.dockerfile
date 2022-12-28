FROM ubuntu

RUN apt update -y && \
    apt install -y python3 python3-pip && \
    pip3 install --upgrade pip

WORKDIR /app

ADD authentication/requirements.txt .

RUN pip3 install -r requirements.txt

COPY authentication/migrate.py authentication/models.py authentication/configuration.py ./

ENTRYPOINT ["python3", "/app/migrate.py"]
