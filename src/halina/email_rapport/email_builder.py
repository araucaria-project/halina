import logging
from jinja2 import Environment, FileSystemLoader
import os
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailBuilder:
    def __init__(self, from_email, to_email, subject, template_name, context, image_path=None):
        self._from_email = from_email
        self._to_email = to_email
        self._subject = subject
        self._template_name = template_name
        self._context = context
        self._image_path = image_path

    async def build(self) -> MIMEMultipart:
        if not all([self._from_email, self._to_email, self._subject, self._template_name, self._context]):
            raise ValueError("All email parameters must be set before building the email")

        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template(self._template_name)
        content = template.render(self._context)

        # Create a MIMEMultipart message
        message = MIMEMultipart("related")
        message["From"] = self._from_email
        message["To"] = self._to_email
        message["Subject"] = self._subject

        # Attach the HTML content
        message.attach(MIMEText(content, "html"))

        if self._image_path:
            with open(self._image_path, 'rb') as img:
                img_data = img.read()
            image = MIMEImage(img_data)
            image.add_header('Content-ID', '<image1>')
            image.add_header('Content-Disposition', 'inline', filename='image1.png')
            message.attach(image)

        return message
