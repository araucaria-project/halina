import logging
from jinja2 import Environment, FileSystemLoader
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import aiofiles

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailBuilder:
    def __init__(self):
        self._subject = None
        self._night = None
        self._total_fits = None
        self._zb08 = None
        self._jk15 = None
        self._table_data = None
        self._image_path = "src/halina/email_rapport/resources/zdjecie.png"

    def set_subject(self, subject):
        self._subject = subject

    def subject(self, subject):
        self.set_subject(subject)
        return self

    def set_night(self, night):
        self._night = night

    def night(self, night):
        self.set_night(night)
        return self

    def set_total_fits(self, total_fits):
        self._total_fits = total_fits

    def total_fits(self, total_fits):
        self.set_total_fits(total_fits)
        return self

    def set_zb08(self, zb08):
        self._zb08 = zb08

    def zb08(self, zb08):
        self.set_zb08(zb08)
        return self

    def set_jk15(self, jk15):
        self._jk15 = jk15

    def jk15(self, jk15):
        self.set_jk15(jk15)
        return self

    def set_table_data(self, table_data):
        self._table_data = table_data

    def table_data(self, table_data):
        self.set_table_data(table_data)
        return self

    async def build(self) -> MIMEMultipart:
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template("resources/email_template.html")
        context = {
            'night': self._night,
            'total_fits': self._total_fits,
            'zb08': self._zb08,
            'jk15': self._jk15,
            'table_data': self._table_data
        }
        content = template.render(context)

        # Create message
        message = MIMEMultipart("related")

        message["Subject"] = self._subject

        # Attach HTML
        message.attach(MIMEText(content, "html"))

        async with aiofiles.open(self._image_path, 'rb') as img:
            img_data = await img.read()
        image = MIMEImage(img_data)
        image.add_header('Content-ID', '<image1>')
        image.add_header('Content-Disposition', 'inline', filename="zdjecie.png")
        message.attach(image)

        return message
