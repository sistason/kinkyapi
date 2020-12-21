FROM python:3.9

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8080
WORKDIR /opt/kinkyapi

COPY src /opt/kinkyapi
COPY entrypoint.sh /opt/kinkyapi/

ENTRYPOINT ["/bin/sh", "/opt/kinkyapi/entrypoint.sh"]
