FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY store/daemon_application.py ./application.py
COPY store/configuration.py ./configuration.py
COPY store/models.py ./models.py
COPY store/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/authentication"

ENTRYPOINT ["python", "./application.py"]