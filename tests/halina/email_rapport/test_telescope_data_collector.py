import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from halina.email_rapport.data_collector_classes.data_object import DataObject
from halina.email_rapport.telescope_data_collector import TelescopeDtaCollector
import json

class TestTelescopeDataCollector(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # print("setUp")
        self.collector = TelescopeDtaCollector(telescope_name="test_telescope", utc_offset=0)

    async def asyncSetUp(self):
        # print("async setUp")
        self.collector = TelescopeDtaCollector(telescope_name="test_telescope", utc_offset=0)

    async def asyncTearDown(self):
        await asyncio.sleep(0)  # Perform any necessary cleanup here

    async def test__validate_download(self):
        json_file_path = "tests/mock/download.json"
        with open(json_file_path, 'r') as file:
            valid_data = json.load(file)

        self.assertTrue(self.collector._validate_download(valid_data, "mock_stream"))

        invalid_data = valid_data.copy()
        invalid_data["fits_id"] = invalid_data.pop("fits_id")
        self.assertFalse(self.collector._validate_download(invalid_data, "mock_stream"))
