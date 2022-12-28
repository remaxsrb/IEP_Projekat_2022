FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY store/admin/migrate.py ./migrate.py
COPY store/admin/configuration.py ./configuration.py
COPY store/admin/models.py ./models.py
COPY store/admin/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./migrate.py"]