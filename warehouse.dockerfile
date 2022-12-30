FROM python:3

RUN mkdir -p /opt/src/store
WORKDIR /opt/src/store

COPY store/warehouse_application.py ./application.py
COPY store/configuration.py ./configuration.py
COPY store/roleCheck.py ./roleCheck.py
COPY store/models.py ./models.py
COPY store/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/store"

ENTRYPOINT ["python", "./application.py"]