FROM python:3.10-slim

# Install ping
RUN apt-get update && apt-get install -y iputils-ping

WORKDIR ./
COPY . /.

RUN pip install poetry
RUN ["poetry", "install"]
STOPSIGNAL SIGINT
ENTRYPOINT ["poetry", "run", "services"]
