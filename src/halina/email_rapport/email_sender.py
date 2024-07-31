"""
Email Sender module.

This module defines the EmailSender class which handles the sending of emails using SMTP.

Classes:
    - EmailSender: Sends emails using SMTP.
"""

import asyncio
import logging
from aiosmtplib import SMTP, SMTPException
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from configuration import GlobalConfig

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailSender:
    """
    EmailSender handles the sending of emails using SMTP.

    Attributes:
        to_email (str): The recipient's email address.
    """

    def __init__(self, to_email: str):
        """
        Initializes the EmailSender with the recipient's email address.

        Args:
            to_email (str): The recipient's email address.
        """
        self.to_email: str = to_email

    async def send(self, message: MIMEMultipart) -> bool:
        """
        Sends an email message using SMTP.

        Args:
            message (MIMEMultipart): The email message to be sent.

        Returns:
            bool: True if the email was sent successfully, False otherwise.

        Raises:
            ValueError: If the email app password is not set in the configuration.
        """
        from_email = GlobalConfig.get(GlobalConfig.FROM_EMAIL)
        email_app_password = GlobalConfig.get(GlobalConfig.SMTP_PASSWORD)
        user_name = GlobalConfig.get(GlobalConfig.SMTP_USERNAME)
        from_name = GlobalConfig.get(GlobalConfig.FROM_NAME)


        if not email_app_password:
            logger.error("Email app password is required but not set.")
            raise ValueError("Email app password is required but not set.")
        logger.info(f"Email name: {user_name}")

        # Set the "From" header with the display name and email address
        message["From"] = formataddr((from_name, from_email))
        message["To"] = self.to_email

        smtp: SMTP = SMTP(hostname=GlobalConfig.get(GlobalConfig.SMTP_HOST),
                          port=GlobalConfig.get(GlobalConfig.SMTP_PORT),
                          start_tls=True)
        try:
            async with smtp:
                await smtp.login(user_name, email_app_password)
                await smtp.send_message(message)
                logger.info(f"Email sent successfully to {self.to_email}")
                return True
        except SMTPException as e:
            logger.error(f"Failed to send email due to SMTP error: {str(e)}")
            return False
