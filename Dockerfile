FROM python:3-alpine

WORKDIR /app/backend

# install firefox
RUN apk add firefox

# install pip requirements
COPY ./requirements.txt /app/init/requirements.txt
RUN cd /app/init/ && pip install --no-cache-dir -r requirements.txt

CMD ["python3", "-u", "app.py"]