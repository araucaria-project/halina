import json
import random
import string
import logging
from serverish.messenger import Messenger
import aiofiles
from pyaraucaria.date import datetime_to_julian
import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DataPublisher:
    FILTER_OPTIONS = string.ascii_uppercase

    FILE_PATHS = {
        "raw": "src/simulator/raw.json",
        "zdf": "src/simulator/zdf.json",
        "download": "src/simulator/download.json"
    }

    def __init__(self, telescopes=None):
        self.telescopes = telescopes or ["zb08", "jk15"]

    @staticmethod
    async def read_json(data_type):
        file_path = DataPublisher.FILE_PATHS.get(data_type)
        if not file_path:
            logger.error(f"Invalid data type: {data_type}")
            raise ValueError("Invalid data type. Choose 'raw', 'zdf', or 'download'.")

        async with aiofiles.open(file_path, 'r') as file:
            data = await file.read()
            return json.loads(data)

    @staticmethod
    def generate_unique_id(length=8):
        unique_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        return unique_id

    @staticmethod
    def generate_random_values(num_copies, telescope):
        logger.info(f"Generating random values for {num_copies} copies for telescope {telescope}")
        random_values = []
        for i in range(num_copies):
            now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=8)
            date_obs = now.isoformat(sep='T', timespec='auto')
            jd = datetime_to_julian(now)
            values = {
                "id": DataPublisher.generate_unique_id(),
                "TELESCOP": telescope,
                "FILTER": random.choice(DataPublisher.FILTER_OPTIONS),
                "OBJECT_NAME": f"w_tuc{i + 1}",
                "DATE-OBS": date_obs,
                "JD": jd
            }
            random_values.append(values)
            logger.debug(f"Generated values: {values}")
        return random_values

    @staticmethod
    def dt_utcnow_array():
        now = datetime.datetime.now(datetime.timezone.utc)
        utcnow_array = [now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond]
        return utcnow_array

    @staticmethod
    def create_copies(original_data, random_values):
        logger.info("Creating raw data copies")
        copies = []
        for values in random_values:
            copy = json.loads(json.dumps(original_data))  # Deep copy
            copy['raw']['header']['TELESCOP'] = values["TELESCOP"]
            copy['raw']['header']['FILTER'] = values["FILTER"]
            copy['fits_id'] = values["id"]
            copy['raw']['header']['OBJECT'] = values["OBJECT_NAME"]
            copy['raw']['header']['DATE-OBS'] = values["DATE-OBS"]
            copy['raw']['header']['JD'] = values["JD"]
            copy['raw']['objects'][values["OBJECT_NAME"]] = copy['raw']['objects'].pop("w_tuc")
            copies.append(copy)
        return copies

    @staticmethod
    def create_zdf_copies(original_data, random_values):
        logger.info("Creating zdf data copies")
        zdf_copies = []
        for values in random_values:
            if random.random() < 0.8:  # 80% chance of occurrence
                copy = json.loads(json.dumps(original_data))  # Deep copy
                copy['zdf']['header']['TELESCOP'] = values["TELESCOP"]
                copy['zdf']['header']['FILTER'] = values["FILTER"]
                copy['fits_id'] = values["id"]
                copy['zdf']['header']['OBJECT'] = values["OBJECT_NAME"]
                copy['zdf']['header']['DATE-OBS'] = values["DATE-OBS"]
                copy['zdf']['header']['JD'] = values["JD"]
                copy['zdf']['objects'][values["OBJECT_NAME"]] = copy['zdf']['objects'].pop("w_tuc")
                zdf_copies.append(copy)
            else:
                zdf_copies.append({})  # Empty record
        return zdf_copies

    @staticmethod
    def create_download_copies(original_data, random_values):
        logger.info("Creating download data copies")
        download_copies = []
        for values in random_values:
            copy = json.loads(json.dumps(original_data))  # Deep copy
            copy['param']['filter'] = values["FILTER"]
            copy['param']['date_obs'] = values["DATE-OBS"]
            copy['param']['target_name'] = values["OBJECT_NAME"]
            copy['telescope_id'] = values["TELESCOP"]
            copy['ts'] = DataPublisher.dt_utcnow_array()
            copy['fits_id'] = values["id"]
            download_copies.append(copy)
        return download_copies

    @staticmethod
    async def publish_data(telescope, stream, data, host, port):
        messenger = Messenger()
        await messenger.open(host, port, wait=5)
        if stream == "download":
            publisher = messenger.get_publisher(f"tic.status.{telescope}.download")
        else:
            publisher = messenger.get_publisher(f"tic.status.{telescope}.fits.pipeline.{stream}")
        await publisher.publish(data)
        await messenger.close()
