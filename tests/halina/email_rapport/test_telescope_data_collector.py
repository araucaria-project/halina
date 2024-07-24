import unittest
from unittest.mock import patch, AsyncMock
import asyncio
from halina.email_rapport.telescope_data_collector import TelescopeDtaCollector
import json
import copy
import definitions


class TestTelescopeDataCollector(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.collector = TelescopeDtaCollector(telescope_name="test_telescope", utc_offset=0)

    async def asyncSetUp(self):
        self.collector = TelescopeDtaCollector(telescope_name="test_telescope", utc_offset=0)

    async def test__validate_download(self) -> None:
        json_file_path = definitions.DOWNLOAD_JSON
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
        json_files = {
            "raw": definitions.RAW_JSON,
            "zdf": definitions.ZDF_JSON
        }
        for key, json_file in json_files.items():
            with open(json_file, 'r') as file:
                valid_data = json.load(file)

            # Check valid data
            self.assertTrue(self.collector._validate_record(valid_data, "mock_stream", key), "Valid data should pass validation")

            # Check invalid data
            invalid_fitsid = valid_data.copy()
            invalid_fitsid["no_fits_id"] = invalid_fitsid.pop("fits_id")
            self.assertFalse(self.collector._validate_record(invalid_fitsid, "mock_stream", key), "Invalid data should fail validation")

            # Check invalid data
            invalid_key = valid_data.copy()
            invalid_key["no_key"] = invalid_key.pop(key)
            self.assertFalse(self.collector._validate_record(invalid_key, "mock_stream", key), "Invalid data should fail validation")

            # Check invalid data
            invalid_header = copy.deepcopy(valid_data)
            invalid_header[key]["no_header"] = invalid_header[key].pop("header")
            self.assertFalse(self.collector._validate_record(invalid_header, "mock_stream", key), "Invalid data should fail validation")

            # Check invalid data
            invalid_jd = copy.deepcopy(valid_data)
            invalid_jd[key]["header"]["no_JD"] = invalid_jd[key]["header"].pop("JD")
            self.assertFalse(self.collector._validate_record(invalid_jd, "mock_stream", key), "Invalid data should fail validation")

    async def test__process_pair(self) -> None:
        # Load data from files
        download_path = definitions.DOWNLOAD_JSON
        raw_path = definitions.RAW_JSON
        zdf_path = definitions.ZDF_JSON

        with open(download_path, 'r') as file:
            download_data = json.load(file)
        with open(raw_path, 'r') as file:
            raw_data = json.load(file)
        with open(zdf_path, 'r') as file:
            zdf_data = json.load(file)

        # Combine data into a single dictionary without raw
        not_raw_data = {
            "download": download_data,
            "zdf": zdf_data
        }
        await self.collector._process_pair(not_raw_data)
        self.assertEqual(self.collector.count_fits, 0, "count_fits should be 0 when raw data is missing")

        # Combine data into a single dictionary with raw
        data = {
            "download": download_data,
            "raw": raw_data,
            "zdf": zdf_data
        }
        await self.collector._process_pair(data)
        self.assertEqual(self.collector.count_fits_processed, 1, "count_fits_processed should be 1")
        self.assertEqual(self.collector.count_fits, 1, "count_fits should be 1")

        # TODO Check the counts of each object in the collector
        # self.assertEqual(len(self.collector.objects), 1, "There should be exactly 1 object in the collector")
        # for obj_name, obj in self.collector.objects.items():
        #     print(f"Object: {obj_name}, Count: {obj.count}")
        #     self.assertEqual(obj.count, 1, f"Object {obj_name} should have count 1")

    async def test__count_malformed_fits(self):
        # Test for raw data
        self.collector._count_malformed_fits(TelescopeDtaCollector._STR_NAME_RAW)
        self.assertEqual(self.collector.malformed_raw_count, 1, "malformed_raw_count should be 1 after counting one malformed raw fit")

        # Test for zdf data
        self.collector._count_malformed_fits(TelescopeDtaCollector._STR_NAME_ZDF)
        self.assertEqual(self.collector.malformed_zdf_count, 1, "malformed_zdf_count should be 1 after counting one malformed zdf fit")

        # Test for download data
        self.collector._count_malformed_fits(TelescopeDtaCollector._STR_NAME_DOWNLOAD)
        self.assertEqual(self.collector.malformed_download_count, 1, "malformed_download_count should be 1 after counting one malformed download fit")

    @patch('halina.email_rapport.telescope_data_collector.TelescopeDtaCollector._process_pair', new_callable=AsyncMock)
    async def test__evaluate_data(self, mock_process_pair):
        self.collector._fits_pair = {
            "id1": {"raw": "data_raw", "zdf": "data_zdf", "download": "data_download"},
            "id2": {"raw": "data_raw"}
        }
        self.collector._unchecked_ids = {"id1", "id2"}
        self.collector._finish_reading_streams = 1  # Mniej niż _NUMBER_STREAMS

        task = asyncio.create_task(self.collector._evaluate_data())
        await asyncio.sleep(0.1)

        # Symulacja zakończenia wszystkich strumieni
        self.collector._finish_reading_streams = 3
        async with self.collector._fp_condition:
            self.collector._fp_condition.notify_all()

        await task

        # Upewnienie się że odpowiednie pary zostały przetworzone
        expected_calls = [
            unittest.mock.call({"raw": "data_raw", "zdf": "data_zdf", "download": "data_download"}),
            unittest.mock.call({"raw": "data_raw"})
        ]
        mock_process_pair.assert_has_awaits(expected_calls, any_order=True)

        # Upewnij się, że _unchecked_ids jest zresetowane, a pozostałe pary zostały przetworzone
        self.assertEqual(self.collector._unchecked_ids, set())
        self.assertEqual(mock_process_pair.await_count, 2)


if __name__ == '__main__':
    unittest.main()