import asyncio
import logging
from aiosmtplib import SMTP, SMTPException
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailSender:
    EMAIL_APP_PASSWORD = 'wynw wprc pzmi hojj'
    FROM_EMAIL = 'dchmal@akond.com'
    SMTP_HOST = 'smtp.gmail.com'
    SMTP_PORT = 587

    def __init__(self, to_email: str):
        self.to_email = to_email

    async def send(self, message: MIMEMultipart):
        message["From"] = EmailSender.FROM_EMAIL
        message["To"] = self.to_email

        smtp = SMTP(hostname=self.SMTP_HOST, port=self.SMTP_PORT, start_tls=True)

        try:
            async with smtp:
                await smtp.login(self.FROM_EMAIL, self.EMAIL_APP_PASSWORD)
                await smtp.send_message(message)
                logger.info(f"Email sent successfully to {self.to_email}")
                return True
        except SMTPException as e:
            logger.error(f"Failed to send email due to SMTP error: {str(e)}")
            return False