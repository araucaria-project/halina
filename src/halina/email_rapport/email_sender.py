import asyncio
import logging
from aiosmtplib import SMTP, SMTPException
from email.mime.multipart import MIMEMultipart

from configuration import GlobalConfig

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailSender:
    def __init__(self, to_email: str):
        self.to_email: str = to_email

    async def send(self, message: MIMEMultipart) -> bool:
        from_email = GlobalConfig.get(GlobalConfig.FROM_EMAIL)
        email_app_password = GlobalConfig.get(GlobalConfig.EMAIL_APP_PASSWORD)
        if not email_app_password:
            logger.error("Email app password is required but not set.")
            raise ValueError("Email app password is required but not set.")

        message["From"] = from_email
        message["To"] = self.to_email

        smtp: SMTP = SMTP(hostname=GlobalConfig.get(GlobalConfig.SMTP_HOST),
                          port=GlobalConfig.get(GlobalConfig.SMTP_PORT),
                          start_tls=True)

        try:
            async with smtp:
                await smtp.login(from_email, email_app_password)
                await smtp.send_message(message)
                logger.info(f"Email sent successfully to {self.to_email}")
                return True
        except SMTPException as e:
            logger.error(f"Failed to send email due to SMTP error: {str(e)}")
            return False
