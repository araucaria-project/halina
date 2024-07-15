import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from halina.email_rapport.data_collector_classes.data_object import DataObject
from halina.email_rapport.telescope_data_collector import TelescopeDtaCollector
import json
import copy


class TestTelescopeDataCollector(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.collector = TelescopeDtaCollector(telescope_name="test_telescope", utc_offset=0)

    async def asyncSetUp(self):
        pass
        # self.collector = TelescopeDtaCollector(telescope_name="test_telescope", utc_offset=0)

    async def test__validate_download(self) -> None:
        json_file_path = "tests/mock/download.json"
        with open(json_file_path, 'r') as file:
            valid_data = json.load(file)

        # Check valid data
        self.assertTrue(self.collector._validate_download(valid_data, "mock_stream"), "Valid data should pass validation")

        # Check invalid data
        invalid_fitsid = valid_data.copy()
        invalid_fitsid["no_fits_id"] = invalid_fitsid.pop("fits_id")
        self.assertFalse(self.collector._validate_download(invalid_fitsid, "mock_stream"), "Invalid data should fail validation")

        # Check invalid data
        invalid_dateobs = valid_data.copy()
        invalid_dateobs["param"]["no_date_obs"] = invalid_dateobs["param"].pop("date_obs")
        self.assertFalse(self.collector._validate_download(invalid_dateobs, "mock_stream"), "Invalid data should fail validation")

    async def test__validate_record(self) -> None:
        json_files = {"raw": "tests/mock/raw.json", "zdf": "tests/mock/zdf.json"}
        for key, json_file in json_files.items():
            with open(json_file, 'r') as file:
                valid_data = json.load(file)

            # Check valid data
            self.assertTrue(self.collector._validate_record(valid_data, "mock_stream", key), "Valid data should pass validation")

            # Check invalid data
            invalid_fitsid = valid_data.copy()
            invalid_fitsid["no_fits_id"] = invalid_fitsid.pop("fits_id")
            self.assertFalse(self.collector._validate_download(invalid_fitsid, "mock_stream"), "Invalid data should fail validation")

            # Check invalid data
            invalid_key = valid_data.copy()
            invalid_key["no_key"] = invalid_key.pop(key)
            self.assertFalse(self.collector._validate_download(invalid_key, "mock_stream"), "Invalid data should fail validation")

            # Check invalid data
            invalid_header = copy.deepcopy(valid_data)
            invalid_header[key]["no_header"] = invalid_header[key].pop("header")
            self.assertFalse(self.collector._validate_download(invalid_header, "mock_stream"), "Invalid data should fail validation")

            # Check invalid data
            invalid_jd = copy.deepcopy(valid_data)
            invalid_jd[key]["header"]["no_JD"] = invalid_jd[key]["header"].pop("JD")
            self.assertFalse(self.collector._validate_download(invalid_jd, "mock_stream"), "Invalid data should fail validation")

    async def test__process_pair(self) -> None:
        # Load data from files
        with open("tests/mock/download.json", 'r') as file:
            download_data = json.load(file)
        with open("tests/mock/raw.json", 'r') as file:
            raw_data = json.load(file)
        with open("tests/mock/zdf.json", 'r') as file:
            zdf_data = json.load(file)

        # Combine data into a single dictionary
        not_raw_data = {
            "download": download_data,
            "zdf": zdf_data
        }
        await self.collector._process_pair(not_raw_data)
        self.assertEqual(self.collector.count_fits, 0,"Valid data should pass validation and increase count_fits")

        # Combine data into a single dictionary
        data = {
            "download": download_data,
            "raw": raw_data,
            "zdf": zdf_data
        }
        await self.collector._process_pair(data)
        self.assertEqual(self.collector.count_fits_processed, 1, "Valid data should pass validation and increase count_fits_processed")
        self.assertEqual(self.collector.count_fits, 1, "Valid data should pass validation and increase count_fits")

        print(len(self.collector.objects))
        for object in self.collector.objects:
            print(f"count: {object.count}")

if __name__ == '__main__':
    unittest.main()
