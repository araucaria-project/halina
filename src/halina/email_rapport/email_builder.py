import logging
from jinja2 import Environment, FileSystemLoader
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailBuilder:
    def __init__(self):
        self._subject = None
        self._template_name = None
        self._context = None
        self._image_path = None

    def set_subject(self, subject):
        self._subject = subject

    def subject(self, subject):
        self.set_subject(subject)
        return self

    def set_template_name(self, template_name):
        self._template_name = template_name

    def template_name(self, template_name):
        self.set_template_name(template_name)
        return self

    def set_context(self, context):
        self._context = context

    def context(self, context):
        self.set_context(context)
        return self

    def set_image_path(self, image_path):
        self._image_path = image_path

    def image_path(self, image_path):
        self.set_image_path(image_path)
        return self

    async def build(self) -> MIMEMultipart:
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template(self._template_name)
        content = template.render(self._context)

        # Create a MIMEMultipart message
        message = MIMEMultipart("related")

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
