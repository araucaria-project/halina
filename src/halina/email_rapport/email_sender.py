import asyncio
import logging
from aiosmtplib import SMTP, SMTPException
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .email_builder import generate_email_content

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailSender:
    EMAIL_APP_PASSWORD = ''
    FROM_EMAIL = 'dchmal@akond.com'
    SMTP_HOST = 'smtp.gmail.com'
    SMTP_PORT = 587

    def __init__(self, to_email, subject, template_name, context, image_path=None):
        self.to_email = to_email
        self.subject = subject
        self.template_name = template_name
        self.context = context
        self.image_path = image_path

    async def send(self):
        message = generate_email_content(
            from_email=self.FROM_EMAIL,
            to_email=self.to_email,
            subject=self.subject,
            template_name=self.template_name,
            context=self.context,
            image_path=self.image_path
        )

        smtp = SMTP(hostname=self.SMTP_HOST, port=self.SMTP_PORT, start_tls=True)

        if self.image_path:
            with open(self.image_path, 'rb') as img:
                img_data = img.read()
            image = MIMEImage(img_data)
            image.add_header('Content-ID', '<image1>')
            image.add_header('Content-Disposition', 'inline', filename='image1.png')
            message.attach(image)

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
        except asyncio.TimeoutError:
            logger.error("Failed to send email due to a timeout error")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return False
