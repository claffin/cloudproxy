FROM nikolaik/python-nodejs:python3.11-nodejs16

ENV PYTHONPATH "$PYTHONPATH:/app"

EXPOSE 8000

COPY . /app
WORKDIR /app/cloudproxy-ui

RUN npm install
RUN npm run build

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python","./cloudproxy/main.py"]