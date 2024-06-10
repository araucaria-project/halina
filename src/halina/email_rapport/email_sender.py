import asyncio
import logging
from email.message import EmailMessage
from aiosmtplib import SMTP, SMTPException

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailSender:
    SENDGRID_API_KEY = 'API'
    FROM_EMAIL = 'dchmal@akond.com'
    SMTP_HOST = 'smtp.sendgrid.net'
    SMTP_PORT = 587

    def __init__(self, to_email, subject, content):
        self.to_email = to_email
        self.subject = subject
        self.content = content

    async def send(self):
        message = EmailMessage()
        message["From"] = self.FROM_EMAIL
        message["To"] = self.to_email
        message["Subject"] = self.subject
        message.set_content(self.content)

        smtp = SMTP(hostname=self.SMTP_HOST, port=self.SMTP_PORT, start_tls=True)

        try:
            await smtp.connect()
            await smtp.login("apikey", self.SENDGRID_API_KEY)
            await smtp.send_message(message)
            await smtp.quit()
            logger.info(f"Email sent successfully to {self.to_email}")
            return True
        except SMTPException as e:
            logger.error(f"Failed to send email due to SMTP error: {str(e)}")
            return False
        except asyncio.TimeoutError:
            logger.error("Failed to send email due to a timeout error")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return False
