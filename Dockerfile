# Created following https://fastapi.tiangolo.com/lo/deployment/docker/#dockerfile
FROM python:3.10


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./wApp /code/wApp

CMD ["uvicorn", "wApp.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]