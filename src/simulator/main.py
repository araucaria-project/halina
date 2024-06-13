import json
import random
import asyncio
import aiofiles
import string

TELESCOP_OPTIONS = ["zb08", "jk15"]
FILTER_OPTIONS = string.ascii_uppercase

async def read_json(file_path):
    async with aiofiles.open(file_path, 'r') as file:
        data = await file.read()
        return json.loads(data)

async def write_json(file_path, data):
    async with aiofiles.open(file_path, 'w') as file:
        await file.write(json.dumps(data, indent=4))

def generate_random_values(num_copies):
    random_values = []
    for i in range(num_copies):
        random_values.append({
            "id": i + 1,
            "TELESCOP": random.choice(TELESCOP_OPTIONS),
            "FILTER": random.choice(FILTER_OPTIONS),
            "OBJECT_NAME": f"w_tuc{i + 1}"
        })
    return random_values

async def create_copies(original_data, random_values):
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

async def create_zdf_copies(original_data, random_values):
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

async def main():
    raw_input_file_path = 'src/simulator/raw.json'
    zdf_input_file_path = 'src/simulator/zdf.json'
    raw_output_file_path = 'src/simulator/raw_copy.json'
    zdf_output_file_path = 'src/simulator/zdf_copy.json'
    num_copies = 10

    raw_original_data = await read_json(raw_input_file_path)
    zdf_original_data = await read_json(zdf_input_file_path)
    random_values = generate_random_values(num_copies)

    raw_copies = await create_copies(raw_original_data, random_values)
    zdf_copies = await create_zdf_copies(zdf_original_data, random_values)

    await write_json(raw_output_file_path, raw_copies)
    await write_json(zdf_output_file_path, zdf_copies)

if __name__ == "__main__":
    asyncio.run(main())
