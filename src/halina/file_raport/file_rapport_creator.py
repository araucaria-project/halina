import asyncio
import json
import logging
import os
import aiofiles

from configuration import GlobalConfig

logger = logging.getLogger(__name__.rsplit('.')[-1])


class FileRapportCreator:

    def __init__(self):
        self._filename: str = 'default.json'
        self._data: dict = {}
        self._subdir: str = ''

    def set_filename(self, filename: str):
        self._filename = filename

    def set_data(self, data: dict):
        self._data = data

    def set_subdir(self, subdir: str):
        self._subdir = subdir

    async def save(self) -> bool:
        path_target = GlobalConfig.get(GlobalConfig.RAPPORT_FILE_TARGET_PATH, '')
        if not path_target:
            return False
        dictionary = self._data
        # Serializing json
        try:
            json_object = json.dumps(dictionary, indent=4)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except TypeError:
            logger.warning("Unable to serialize the object to JSON")
            return False
        except Exception as e:
            logger.error(f'Error handle when try to serialize data to json. Error: {e}')
            return False
        try:
            # Write to json
            async with aiofiles.open(os.path.join(path_target, self._subdir, self._filename), 'w') as file:
                await file.write(json_object)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception as e:
            logger.error(f'Error handle when try to write json file. Error: {e}')
            return False
        return True
