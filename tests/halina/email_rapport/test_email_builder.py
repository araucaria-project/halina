import unittest
from unittest.mock import patch, MagicMock
from email.mime.multipart import MIMEMultipart
from halina.email_rapport.email_builder import EmailBuilder
from halina.email_rapport.data_collector_classes.data_object import DataObject
import logging

# Konfiguracja loggera dla testów
logging.basicConfig(level=logging.INFO)


class TestEmailBuilder(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.email_builder = EmailBuilder()

    def test_set_subject(self):
        self.email_builder.set_subject("Test Subject")
        self.assertEqual(self.email_builder._subject, "Test Subject")

    def test_set_night(self):
        self.email_builder.set_night("2024-07-15")
        self.assertEqual(self.email_builder._night, "2024-07-15")

    def test_set_telescope_data(self):
        telescope_data = [{"name": "Telescope1", "data": "Sample Data"}]
        self.email_builder.set_telescope_data(telescope_data)
        self.assertEqual(self.email_builder._telescope_data, telescope_data)

    def test_set_data_objects(self):
        data_objects = {"obj1": DataObject(name="obj1", count=1)}
        self.email_builder.set_data_objects(data_objects)
        self.assertEqual(self.email_builder._data_objects, data_objects)

    @patch('halina.email_rapport.email_builder.FileSystemLoader')
    @patch('halina.email_rapport.email_builder.Environment.get_template')
    @patch('halina.email_rapport.email_builder.aiofiles.open', new_callable=MagicMock)
    @patch('halina.email_rapport.email_builder.MIMEImage')
    async def test_build(self, mock_mimeimage, mock_open, mock_get_template, mock_filesystemloader):
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Test Email</html>"
        mock_get_template.return_value = mock_template

        async def mock_read():
            return b"fake_image_data"

        mock_open.return_value.__aenter__.return_value.read = mock_read

        self.email_builder.set_subject("Test Subject")
        self.email_builder.set_night("2024-07-15")
        self.email_builder.set_telescope_data([{"name": "Telescope1", "data": "Sample Data"}])
        self.email_builder.set_data_objects({"obj1": DataObject(name="obj1", count=1)})

        email_message = await self.email_builder.build()

        self.assertIsInstance(email_message, MIMEMultipart)
        self.assertEqual(email_message["Subject"], "Test Subject")
        self.assertTrue(any(part.get_content_type() == 'text/html' for part in email_message.get_payload()))
        self.assertTrue(mock_open.called)
        self.assertTrue(mock_mimeimage.called)
        self.assertTrue(mock_template.render.called)


if __name__ == '__main__':
    unittest.main()
