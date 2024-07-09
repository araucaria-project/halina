FROM python:3.10-slim

# Install ping
RUN apt-get update && apt-get install -y iputils-ping

WORKDIR /app
COPY . /app

RUN pip install poetry
RUN poetry install

CMD ["poetry", "run", "services"]
