import logging
from jinja2 import Environment, FileSystemLoader
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import aiofiles
from typing import List, Dict, Any
from halina.email_rapport.data_collector_classes.data_object import DataObject

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailBuilder:
    def __init__(self):
        self._subject: str = ""
        self._night: str = ""
        self._telescope_data: List[Dict[str, Any]] = []
        self._data_objects: Dict[str, DataObject] = {}
        self._image_path: str = "src/halina/email_rapport/resources/zdjecie.png"
        self._logo_path: str = "src/halina/email_rapport/resources/araucaria_logo.png"

    def set_subject(self, subject: str) -> None:
        self._subject = subject

    def subject(self, subject: str) -> 'EmailBuilder':
        self.set_subject(subject)
        return self

    def set_night(self, night: str) -> None:
        self._night = night
        logger.info(f"Night set to: {night}")

    def night(self, night: str) -> 'EmailBuilder':
        self.set_night(night)
        return self

    def set_telescope_data(self, telescope_data: List[Dict[str, Any]]) -> None:
        self._telescope_data = telescope_data
        logger.info(f"Telescope data set.")

    def telescope_data(self, telescope_data: List[Dict[str, Any]]) -> 'EmailBuilder':
        self.set_telescope_data(telescope_data)
        return self

    def set_data_objects(self, data_objects: Dict[str, DataObject]) -> None:
        self._data_objects = data_objects
        logger.info(f"Data objects set.")

    def data_objects(self, data_objects: Dict[str, DataObject]) -> 'EmailBuilder':
        self.set_data_objects(data_objects)
        return self

    async def build(self) -> MIMEMultipart:
        logger.info("Building the email.")
        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template("resources/email_template.html")
        context = {
            'night': self._night,
            'telescope_data': self._telescope_data,
            'data_objects': self._data_objects
        }
        content = template.render(context)

        # Create message
        message = MIMEMultipart("related")
        message["Subject"] = self._subject

        # Attach HTML
        message.attach(MIMEText(content, "html"))
        logger.info("HTML content attached to email.")

        # async with aiofiles.open(self._image_path, 'rb') as img:
        #     img_data = await img.read()
        # image = MIMEImage(img_data)
        # image.add_header('Content-ID', '<image1>')
        # image.add_header('Content-Disposition', 'inline', filename="zdjecie.png")
        # message.attach(image)

        # Attach logo
        async with aiofiles.open(self._logo_path, 'rb') as logo:
            logo_data = await logo.read()
        logo_image = MIMEImage(logo_data)
        logo_image.add_header('Content-ID', '<logo>')
        logo_image.add_header('Content-Disposition', 'inline', filename="araucaria_logo.png")
        message.attach(logo_image)
        logger.info("Logo image attached to email.")

        return message
