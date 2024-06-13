import asyncio
import json
from .data_publisher import DataPublisher

async def main():
    raw_input_file_path = 'src/simulator/raw.json'
    zdf_input_file_path = 'src/simulator/zdf.json'
    num_copies = 10

    data_publisher = DataPublisher()

    raw_original_data = await data_publisher.read_json(raw_input_file_path)
    zdf_original_data = await data_publisher.read_json(zdf_input_file_path)

    random_values = data_publisher.generate_random_values(num_copies)
    raw_copies = data_publisher.create_copies(raw_original_data, random_values)
    zdf_copies = data_publisher.create_zdf_copies(zdf_original_data, random_values)

    for raw, zdf in zip(raw_copies, zdf_copies):
        raw_data = json.dumps(raw)
        await data_publisher.publish_data("tic.status.testtel.fits.pipeline.raw", raw_data)
        if zdf:  # Publikuj tylko niepuste rekordy
            zdf_data = json.dumps(zdf)
            await data_publisher.publish_data("tic.status.testtel.fits.pipeline.zdf", zdf_data)

if __name__ == "__main__":
    asyncio.run(main())
