# data_publisher.py
import json
import random
import string
from serverish.messenger import Messenger
import aiofiles
from pyaraucaria.date import datetime_to_julian
import datetime


class DataPublisher:
    FILTER_OPTIONS = string.ascii_uppercase

    FILE_PATHS = {
        "raw": "src/simulator/raw.json",
        "zdf": "src/simulator/zdf.json"
    }

    def __init__(self, telescopes=None):
        self.telescopes = telescopes or ["zb08", "jk15"]

    @staticmethod
    async def read_json(data_type):
        file_path = DataPublisher.FILE_PATHS.get(data_type)
        if not file_path:
            raise ValueError("Invalid data type. Choose 'raw' or 'zdf'.")

        async with aiofiles.open(file_path, 'r') as file:
            data = await file.read()
            return json.loads(data)

    @staticmethod
    def generate_unique_id(length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def generate_random_values(num_copies, telescope):
        random_values = []
        for i in range(num_copies):
            now = datetime.datetime.now(datetime.UTC)
            date_obs = now.isoformat(sep='T', timespec='auto')
            jd = datetime_to_julian(now)
            random_values.append({
                "id": DataPublisher.generate_unique_id(),
                "TELESCOP": telescope,
                "FILTER": random.choice(DataPublisher.FILTER_OPTIONS),
                "OBJECT_NAME": f"w_tuc{i + 1}",
                "DATE-OBS": date_obs,
                "JD": jd
            })
        return random_values

    @staticmethod
    def create_copies(original_data, random_values):
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
        zdf_copies = []
        for values in random_values:
            if random.random() < 0.8:  # 80% szans na wystąpienie
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
                zdf_copies.append({})  # Pusty rekord
        return zdf_copies

    @staticmethod
    async def publish_data(stream, data, host, port):
        messenger = Messenger()
        await messenger.open(host, port, wait=5)
        publisher = messenger.get_publisher(stream)
        await publisher.publish(data)
        await messenger.close()
