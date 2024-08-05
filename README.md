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

The application is configured by creating a TOML file named `settings.toml` and placing it in the appropriate directory or providing 
parameters as command arguments. Configuration files are read sequentially from the locations and if the parameters 
are repeated, they are overwritten.
Locations:
- `./configuration/default_settings.toml`
- `./configuration/settings.toml`
- `/usr/local/etc/halina/settings.toml`
-  command arguments

The following variables can be used to configure the simulator and email report service:

- `NATS_HOST`: NATS server host
- `NATS_PORT`: NATS server port
- `TELESCOPES`: List of telescope names included in HALina analysis.e.g. `["jk15","zb08"]`
- `EMAILS_TO`: List of email addresses to send reports to `["mail1@example.com","mail1@example.com"]`
- `SMTP_HOST`: Server SMTP host name
- `SMTP_PORT`: Server SMTP port
- `SMTP_USERNAME`: SMTP server username 
- `SMTP_PASSWORD`: SMTP server user password  
- `FROM_EMAIL`: Sent emails FROM field email address, e.g. `noreplay.example.com` 
- `FROM_NAME`: Sent emails FROM field display name, e.g. `HALina`
- `SEND_AT`: UTC time at which the data collection process will be started. It is integer number representing hour.

Example `settings.toml` file:

```text
NATS_HOST='localhost'
NATS_PORT=4222
TELESCOPES=['jk15','zb08']
SMTP_HOST='smtp.example.com'
SMTP_PORT=587
SMTP_USERNAME='halina@example.com'
SMTP_PASSWORD='abcdefg'
EMAILS_TO=['mail1@example.com','mail1@example.com']
FROM_EMAIL='noreplay@example.com'
FROM_NAME='Halina'
SEND_AT=14
```
Command arguments
All parameters given as command arguments are read as a string and then parsed into JSON format. It is 
important that parameters marked as JSON types, e.g. (JSON list), are provided in the correct format with the `""` 
symbol inside if needed.

For example
```bash
poetry run services TELESCOPES='["jk15","zb08"]' NATS_PORT=4222
```

WARNING! In some system shells, complex parameters, e.g. list type, set on command line may not work properly. 
So, it is recommended to use the TOML file.

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
