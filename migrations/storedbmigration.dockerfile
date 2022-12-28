FROM ubuntu

RUN apt update -y && \
    apt install -y python3 python3-pip && \
    pip3 install --upgrade pip

WORKDIR /app

ADD store/admin/requirements.txt .

RUN pip3 install -r requirements.txt

COPY store/admin/migrate.py store/admin/models.py store/admin/configuration.py ./

ENTRYPOINT ["python3", "/app/migrate.py"]
