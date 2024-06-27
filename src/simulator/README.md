# Halina Project - Data Simulator

This project is part of the Halina project and focuses on simulating data generation for a set of telescopes and publishing the generated data to a NATS server. The generated data can be used for various purposes, including testing the email report service.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Files](#files)
- [License](#license)

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

### Running the Data Simulator

The data simulator generates and publishes data for a set of telescopes. The data is published to a NATS server specified by the user.

To run the simulator, use the following command:

```bash
poetry run simulator --num_copies 10 --host localhost --port 4222 --telescopes zb08,jk15
```

# Data Simulator

## Arguments

- `--num_copies`: Number of copies to generate for each telescope (default: 10)
- `--host`: NATS server host (default: localhost)
- `--port`: NATS server port (default: 4222)
- `--telescopes`: Comma-separated list of telescope names (default: zb08,jk15)

## Example

To generate and publish 12 copies of data for telescopes zb08 and jk15 to a NATS server running on localhost at port 4222, run:

``` bash 
poetry run simulator --num_copies 12 --host localhost --port 4222 --telescopes zb08,jk15
```

## Configuration

The following environment variables can be used to configure the simulator:

- `NUM_COPIES`: Number of copies to generate for each telescope
- `NATS_HOST`: NATS server host
- `NATS_PORT`: NATS server port
- `TELESCOPES`: Comma-separated list of telescope names

Example usage with environment variables:

``` bash 
export NUM_COPIES=12
export NATS_HOST=localhost
export NATS_PORT=4222
export TELESCOPES=zb08,jk15
poetry run simulator
```

## Files

- `simulator.py`: The main entry point for the data simulator. It generates random values for each telescope, creates copies of the original data, and publishes the data to the NATS server.
- `data_publisher.py`: Contains the `DataPublisher` class responsible for generating random values, creating copies of the original data, and publishing the data to the NATS server.

## Example JSON Files

- `src/simulator/raw.json`: Contains the template for the raw data.
- `src/simulator/zdf.json`: Contains the template for the zdf data.

## License

This project is licensed under the MIT License. See the LICENSE file for details.


