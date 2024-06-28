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

## Usage

### Email Report Service

The email report service collects data from various telescopes, processes it, and sends a summary email report.

To run the email report service, use the following command:

```bash
poetry run services
```

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

## Configuration

The following environment variables can be used to configure the simulator and email report service:

- `NUM_COPIES`: Number of copies to generate for each telescope
- `NATS_HOST`: NATS server host
- `NATS_PORT`: NATS server port
- `TELESCOPES`: Comma-separated list of telescope names
- `EMAILS_TO`: List of email addresses to send reports to

Example usage with environment variables:

```bash 
export NUM_COPIES=12
export NATS_HOST=localhost
export NATS_PORT=4222
export TELESCOPES=zb08,jk15
export EMAILS_TO="email1@example.com,email2@example.com"
poetry run services
```

## Development

To set up a development environment:

1. Clone the repository and install dependencies as described in the Installation section.
2. Run tests to ensure everything is working correctly:
    ```bash
    
    ```
3. Make your changes and commit them to a new branch.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
