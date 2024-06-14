import asyncio
from .data_publisher import DataPublisher
import argparse
import os


async def main(num_copies, host, port, telescopes):
    data_publisher = DataPublisher(telescopes)

    raw_original_data = await data_publisher.read_json('raw')
    zdf_original_data = await data_publisher.read_json('zdf')

    all_raw_copies = []
    all_zdf_copies = []

    for telescope in telescopes:
        random_values = data_publisher.generate_random_values(num_copies, telescope)
        raw_copies = data_publisher.create_copies(raw_original_data, random_values)
        zdf_copies = data_publisher.create_zdf_copies(zdf_original_data, random_values)

        all_raw_copies.extend(raw_copies)
        all_zdf_copies.extend(zdf_copies)

    raw_data_list = []
    zdf_data_list = []

    for raw, zdf in zip(all_raw_copies, all_zdf_copies):
        await data_publisher.publish_data("tic.status.testtel.fits.pipeline.raw", raw, host, port)
        raw_data_list.append(raw)
        if zdf:  # Publikuj tylko niepuste rekordy
            await data_publisher.publish_data("tic.status.testtel.fits.pipeline.zdf", zdf, host, port)
            zdf_data_list.append(zdf)


def run():
    # os.environ['NUM_COPIES'] = '15'
    parser = argparse.ArgumentParser(description="Run the data simulator.")
    parser.add_argument("--num_copies", type=int, default=os.getenv("NUM_COPIES", 10),
                        help="Number of copies to generate for each telescope")
    parser.add_argument("--host", type=str, default=os.getenv("NATS_HOST", "localhost"), help="NATS server host")
    parser.add_argument("--port", type=int, default=os.getenv("NATS_PORT", 4222), help="NATS server port")
    parser.add_argument("--telescopes", type=str, default=os.getenv("TELESCOPES", "zb08,jk15"),
                        help="Comma-separated list of telescopes")
    args = parser.parse_args()

    telescopes = args.telescopes.split(',')

    asyncio.run(main(args.num_copies, args.host, args.port, telescopes))


if __name__ == "__main__":
    run()
