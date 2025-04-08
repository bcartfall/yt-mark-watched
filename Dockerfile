FROM debian:stable-slim

WORKDIR /app/yt-mark-watched

# install packages
RUN apt update && apt upgrade --yes
RUN apt install firefox-esr python3 python3-pip --yes

# install pip requirements
COPY ./requirements.txt /app/init/requirements.txt
RUN rm /usr/lib/python*/EXTERNALLY-MANAGED && cd /app/init/ && pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "-u", "app.py"]