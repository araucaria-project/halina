import asyncio
import logging
from email.message import EmailMessage
from aiosmtplib import SMTP, SMTPException

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailSender:
    EMAIL_APP_PASSWORD = ''
    FROM_EMAIL = 'dchmal@akond.com'
    SMTP_HOST = 'smtp.gmail.com'
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
            await smtp.login(self.FROM_EMAIL, self.EMAIL_APP_PASSWORD)
            await smtp.send_message(message)
            await smtp.quit()
            logger.info(f"Email sent successfully to {self.to_email}")
            print("Udało się wysłać maila")
            return True
        except SMTPException as e:
            logger.error(f"Failed to send email due to SMTP error: {str(e)}")
            print("Nie udało się wysłać maila")
            return False
        except asyncio.TimeoutError:
            logger.error("Failed to send email due to a timeout error")
            print("Nie udało się wysłać maila")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            print("Nie udało się wysłać maila")
            return False

async def main():
    email_sender = EmailSender(
        to_email="d.chmalu@gmail.com",
        subject="Test Email",
        content="Testowy mail do wysyłania raportów z obserwatorium"
    )
    result = await email_sender.send()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())