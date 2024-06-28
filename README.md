# Halina Project

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Email Report Service](#email-report-service)
- [Configuration](#configuration)
- [Development](#development)
- [Files](#files)
- [License](#license)

## Overview

The Halina project is a heuristic algorithmic library designed for managing and processing astronomical observation data. It includes components for simulating data, collecting telescope observations, and sending email reports with the processed data.

## Prerequisites

- Python 3.10 or higher
- NATS server running on your local machine or accessible over the network

## Installation

1. Clone the repository:
    ``` bash
    git clone https://github.com/araucaria-project/halina.git
    cd halina
    ```

2. Install `poetry` if you don't have it installed:
    ``` bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3. Install the dependencies using `poetry`:
    ``` bash
    poetry install
    ```

## Usage

### Email Report Service

The email report service collects data from various telescopes, processes it, and sends a summary email report.

To run the email report service, use the following command:

``` bash
poetry run services
```

## Configuration

The following environment variables can be used to configure the simulator and email report service:

- `NUM_COPIES`: Number of copies to generate for each telescope
- `NATS_HOST`: NATS server host
- `NATS_PORT`: NATS server port
- `TELESCOPES`: Comma-separated list of telescope names
- `EMAILS_TO`: List of email addresses to send reports to

Example usage with environment variables:

``` bash
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
    ``` bash
    
    ```
3. Make your changes and commit them to a new branch.

## Files

### `src/simulator/README.md`

Contains detailed instructions for the data simulator utility, which connects to the NATS server using `serverish.Messenger` and sends fake data to the server. The observation data pretends to come from the telescope `halsim`.

### `asyncio_util_functions.py`

Contains utility functions for working with asyncio.

### `date_utils.py`

Provides utility functions for handling date and time, including converting to Julian dates.

### `email_rapport_service.py`

Collects data from telescopes and sends email reports.

### `email_builder.py`

Builds the email content using Jinja2 templates.

### `email_sender.py`

Sends the generated email using SMTP.

### `telescope_data_collector.py`

Collects data from the telescope data streams.

### `email_rapport/data_collector_classes/data_object.py`

Defines the data object structure for collecting data.

### `main.py`

Entry point for running the application.

### `nats_connection_service.py`

Manages the connection to the NATS server.

### `service.py`

Base class for services used in the project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
