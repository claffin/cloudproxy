FROM python:3.8-slim-buster

ENV PYTHONPATH "$PYTHONPATH:/app"

EXPOSE 8000

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
ENTRYPOINT ["python","./cloudproxy/main.py"]