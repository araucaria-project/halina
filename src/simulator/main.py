import asyncio
import logging
from .data_publisher import DataPublisher
import argparse
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

logging.getLogger('connection_nats').setLevel(logging.WARNING)
logging.getLogger('messenger').setLevel(logging.WARNING)


async def main(num_copies, host, port, telescopes, only_download):
    data_publisher = DataPublisher(telescopes)

    raw_original_data = await data_publisher.read_json('raw')
    zdf_original_data = await data_publisher.read_json('zdf')
    download_original_data = await data_publisher.read_json('download')

    all_raw_copies = []
    all_zdf_copies = []
    all_download_copies = []

    logger.info("Generating random values and creating copies for each telescope")
    for telescope in telescopes:
        random_values = data_publisher.generate_random_values(num_copies, telescope)
        raw_copies = data_publisher.create_copies(raw_original_data, random_values)
        zdf_copies = data_publisher.create_zdf_copies(zdf_original_data, random_values)
        download_copies = data_publisher.create_download_copies(download_original_data, random_values)

        all_raw_copies.extend(raw_copies)
        all_zdf_copies.extend(zdf_copies)
        all_download_copies.extend(download_copies)

    raw_data_list = []
    zdf_data_list = []
    download_data_list = []

    logger.info("Publishing data to NATS server")
    for raw, zdf, download in zip(all_raw_copies, all_zdf_copies, all_download_copies):
        telescope = raw['raw']['header']['TELESCOP']
        await data_publisher.publish_data(telescope, "download", download, host, port)
        download_data_list.append(download)

        if not only_download:
            await data_publisher.publish_data(telescope, "raw", raw, host, port)
            raw_data_list.append(raw)
            if zdf:  # Publish only non-empty records
                await data_publisher.publish_data(telescope, "zdf", zdf, host, port)
                zdf_data_list.append(zdf)

    logger.info("Data publishing completed")


def run():
    parser = argparse.ArgumentParser(description="Run the data simulator.")
    parser.add_argument("--num_copies", type=int, default=os.getenv("NUM_COPIES", 10),
                        help="Number of copies to generate for each telescope")
    parser.add_argument("--host", type=str, default=os.getenv("NATS_HOST", "localhost"), help="NATS server host")
    parser.add_argument("--port", type=int, default=os.getenv("NATS_PORT", 4222), help="NATS server port")
    parser.add_argument("--telescopes", type=str, default=os.getenv("TELESCOPES", "zb08,jk15"),
                        help="Comma-separated list of telescopes")
    parser.add_argument("--only_download", action='store_true', help="If set, only publish download data")

    args = parser.parse_args()

    logger.info(f"Starting data simulator with parameters: {args}")

    telescopes = args.telescopes.split(',')

    asyncio.run(main(args.num_copies, args.host, args.port, telescopes, args.only_download))


if __name__ == "__main__":
    run()
