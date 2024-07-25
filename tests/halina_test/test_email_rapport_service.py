import unittest
from unittest.mock import patch, AsyncMock
from datetime import datetime
from halina.email_rapport_service import SendEmailException, EmailRapportService
from halina.email_rapport.data_collector_classes.data_object import DataObject


class TestEmailRapportService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = EmailRapportService(utc_offset=0)

    def test__format_night_same_month(self):
        with patch('halina.date_utils.DateUtils.yesterday_midday', return_value=datetime(2023, 7, 15)):
            with patch('halina.date_utils.DateUtils.today_midday', return_value=datetime(2023, 7, 16)):
                night = EmailRapportService._format_night()
                self.assertEqual(night, "15-16 Jul 2023")

    def test__format_night_different_months(self):
        with patch('halina.date_utils.DateUtils.yesterday_midday', return_value=datetime(2023, 7, 31)):
            with patch('halina.date_utils.DateUtils.today_midday', return_value=datetime(2023, 8, 1)):
                night = EmailRapportService._format_night()
                self.assertEqual(night, "31 Jul - 1 Aug 2023")

    def test_merge_data_objects(self):
        objects = {
            "obj1": DataObject(name="obj1", count=1, filters={"filter1"}),
            "obj2": DataObject(name="obj1", count=2, filters={"filter2"}),
        }
        merged = self.service.merge_data_objects(objects)
        self.assertEqual(merged["obj1"].count, 3)
        self.assertEqual(merged["obj1"].filters, {"filter1", "filter2"})

    @patch('halina.email_rapport_service.Messenger')
    async def test__collect_data_and_send_no_nats_connection(self, mock_messenger):
        mock_messenger.is_open = False
        self.service._nats_messenger = mock_messenger
        with self.assertRaises(SendEmailException):
            await self.service._collect_data_and_send()

    # _collect_data_and_send

    async def test__main(self):
        with patch.object(self.service, '_collect_data_and_send', new_callable=AsyncMock) as mock_collect_data_and_send:
            await self.service._main()
            mock_collect_data_and_send.assert_awaited()

    async def test__on_start(self):
        await self.service._on_start()  # This should just pass

    async def test__on_stop(self):
        await self.service._on_stop()  # This should just pass


if __name__ == '__main__':
    unittest.main()
