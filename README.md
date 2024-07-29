# Halina Project

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Email Report Service](#email-report-service)
  - [Running the Data Simulator](#running-the-data-simulator)
- [Configuration](#configuration)
- [Development](#development)
- [License](#license)

## Overview

The Halina project is a heuristic algorithmic library designed for managing and processing astronomical observation data. It includes components for simulating data, collecting telescope observations, and sending email reports with the processed data.

## Prerequisites

- Python 3.10 or higher
- NATS server running on your local machine or accessible over the network

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/araucaria-project/halina.git
    cd halina 
    ```

2. Install `poetry` if you don't have it installed:
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3. Install the dependencies using `poetry`:
    ```bash
    poetry install
    ```

## Configuration

The following environment variables can be used to configure the simulator and email report service:

- `NATS_HOST`: NATS server host
- `NATS_PORT`: NATS server port
- `TELESCOPE_NAMES`: list of telescope names if json format for example `'["jk15","zb08"]'`. List type variable
- `EMAILS_TO`: List of email addresses to send reports to in json format `'["mail1@example.com","mail1@example.com"]'`. List type variable
- `SMTP_HOST`: Server SMTP host name
- `SMTP_PORT`: Server SMTP port
- `FROM_EMAIL`: Technical email to sending messages 
- `FROM_EMAIL_USER`: Display name for the email sender
- `EMAIL_APP_PASSWORD`: Password to technical email 
- `SEND_AT`: UTC time at which the data collection process will be started. It is integer number representing hour.

Note. It is important that List type variables are wrapped in `' '`.

Example `.env` file:

```text
NATS_HOST=localhost
NATS_PORT=4222
TELESCOPE_NAMES='["jk15","zb08"]'
EMAILS_TO='["mail1@example.com","mail1@example.com"]'
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=noreply.araucaria
FROM_EMAIL_USER='Araucaria - Night Report'
EMAIL_APP_PASSWORD=abcdefg1234
SEND_AT=14
```

If you are running the application not via Docker, the .env file is not loaded automatically. You must import it manually. 
```bash
env $(cat .env | xargs)
```
It is also possible to set environment variables manually one by one.

It is also possible to configure the application by providing variable values directly as command options. For example: 

```bash
poetry run services TELESCOPE_NAMES='["jk15","zb08"]' NATS_PORT=4222
```

## Usage

### Email Report Service

The email report service collects data from various telescopes, processes it, and sends a summary email report.

To run the email report service, use the following command:

```bash
poetry run services
```

## Development

### Running the Data Simulator

The data simulator generates and publishes data for a set of telescopes. The data is published to a NATS server specified by the user.

To run the simulator, use the following command:

```bash
poetry run simulator --num_copies 10 --host localhost --port 4222 --telescopes zb08,jk15
```

#### Arguments

- `--num_copies`: Number of copies to generate for each telescope (default: 10)
- `--host`: NATS server host (default: localhost)
- `--port`: NATS server port (default: 4222)
- `--telescopes`: Comma-separated list of telescope names (default: zb08,jk15)

#### Example

To generate and publish 12 copies of data for telescopes zb08 and jk15 to a NATS server running on localhost at port 4222, run:

```bash 
poetry run simulator --num_copies 12 --host localhost --port 4222 --telescopes zb08,jk15
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
