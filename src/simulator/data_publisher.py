import json
import random
import string
from serverish.messenger import Messenger
import aiofiles

TELESCOP_OPTIONS = ["zb08", "jk15"]
FILTER_OPTIONS = string.ascii_uppercase

class DataPublisher:
    async def read_json(self, file_path):
        async with aiofiles.open(file_path, 'r') as file:
            data = await file.read()
            return json.loads(data)

    def generate_random_values(self, num_copies):
        random_values = []
        for i in range(num_copies):
            random_values.append({
                "id": i + 1,
                "TELESCOP": random.choice(TELESCOP_OPTIONS),
                "FILTER": random.choice(FILTER_OPTIONS),
                "OBJECT_NAME": f"w_tuc{i + 1}"
            })
        return random_values

    def create_copies(self, original_data, random_values):
        copies = []
        for values in random_values:
            copy = json.loads(json.dumps(original_data))  # Deep copy
            copy['raw']['header']['TELESCOP'] = values["TELESCOP"]
            copy['raw']['header']['FILTER'] = values["FILTER"]
            copy['fits_id'] = values["id"]
            copy['raw']['header']['OBJECT'] = values["OBJECT_NAME"]
            copy['raw']['objects'][values["OBJECT_NAME"]] = copy['raw']['objects'].pop("w_tuc")
            copies.append(copy)
        return copies

    def create_zdf_copies(self, original_data, random_values):
        zdf_copies = []
        for values in random_values:
            if random.random() < 0.8:  # 80% szans na wystąpienie
                copy = json.loads(json.dumps(original_data))  # Deep copy
                copy['zdf']['header']['TELESCOP'] = values["TELESCOP"]
                copy['zdf']['header']['FILTER'] = values["FILTER"]
                copy['fits_id'] = values["id"]
                copy['zdf']['header']['OBJECT'] = values["OBJECT_NAME"]
                copy['zdf']['objects'][values["OBJECT_NAME"]] = copy['zdf']['objects'].pop("w_tuc")
                zdf_copies.append(copy)
            else:
                zdf_copies.append({})  # Pusty rekord
        return zdf_copies

    async def publish_data(self, stream, data):
        messenger = Messenger()
        await messenger.open("localhost", 4222, wait=5)
        publisher = messenger.get_publisher(stream)
        await publisher.publish(data)
        await messenger.close()
