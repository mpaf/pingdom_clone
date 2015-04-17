FROM python:3.4

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN git clone https://github.com/mpaf/pingdom_clone.git /usr/src/app

RUN pip install -r requirements.txt

EXPOSE 8080

CMD [ "python", "/usr/src/app/app.py"]
