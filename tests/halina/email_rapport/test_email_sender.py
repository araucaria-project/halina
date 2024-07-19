import unittest
from unittest.mock import patch, AsyncMock
from email.mime.multipart import MIMEMultipart
from aiosmtplib import SMTPException
from halina.email_rapport.email_sender import EmailSender


class TestEmailSender(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.to_email = "test@example.com"
        self.email_sender = EmailSender(self.to_email)

    @patch('halina.email_rapport.email_sender.GlobalConfig.get')
    @patch('halina.email_rapport.email_sender.SMTP')
    async def test_send_email_success(self, mock_smtp_class, mock_global_config_get):
        # Setup mock
        mock_smtp = mock_smtp_class.return_value
        mock_smtp.__aenter__.return_value = mock_smtp
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock()
        mock_global_config_get.side_effect = lambda x: {
            "FROM_EMAIL": "from@example.com",
            "EMAIL_APP_PASSWORD": "password",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": 587
        }[x]

        message = MIMEMultipart()
        result = await self.email_sender.send(message)

        self.assertTrue(result)
        mock_smtp.login.assert_called_once_with("from@example.com", "password")
        mock_smtp.send_message.assert_called_once_with(message)

    @patch('halina.email_rapport.email_sender.GlobalConfig.get')
    @patch('halina.email_rapport.email_sender.SMTP')
    async def test_send_email_failure(self, mock_smtp_class, mock_global_config_get):
        # Setup mock
        mock_smtp = mock_smtp_class.return_value
        mock_smtp.__aenter__.return_value = mock_smtp
        mock_smtp.login = AsyncMock()
        mock_smtp.send_message = AsyncMock(side_effect=SMTPException("SMTP error"))
        mock_global_config_get.side_effect = lambda x: {
            "FROM_EMAIL": "from@example.com",
            "EMAIL_APP_PASSWORD": "password",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": 587
        }[x]

        message = MIMEMultipart()
        result = await self.email_sender.send(message)

        self.assertFalse(result)
        mock_smtp.login.assert_called_once_with("from@example.com", "password")
        mock_smtp.send_message.assert_called_once_with(message)

    @patch('halina.email_rapport.email_sender.GlobalConfig.get')
    async def test_send_email_no_password(self, mock_global_config_get):
        mock_global_config_get.side_effect = lambda x: {
            "FROM_EMAIL": "from@example.com",
            "EMAIL_APP_PASSWORD": None,
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": 587
        }[x]

        message = MIMEMultipart()
        with self.assertRaises(ValueError):
            await self.email_sender.send(message)


if __name__ == '__main__':
    unittest.main()
