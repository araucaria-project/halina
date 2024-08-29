import logging
from jinja2 import Environment, FileSystemLoader
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import aiofiles
from typing import List, Dict, Any
from definitions import RESOURCES_DIR
from halina.email_rapport.data_collector_classes.data_object import DataObject

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailBuilder:
    _FILENAME_LOGO_AKOND = "logo_akond.png"
    _FILENAME_LOGO_CAMK_PAN = "logo_camk_pan.png"
    _FILENAME_ARAUCARIA_LOGO = "araucaria_logo.png"
    _FILENAME_LOGO_HALINA = "logo_HALina.png"
    _FILENAME_LOGO_OCM = "logo_ENG_granat_wypelniony_srodek.png"
    _EMAIL_TEMPLATE_NAME = "email_template.html"

    def __init__(self):
        self._subject: str = ""
        self._night: str = ""
        self._telescope_data: List[Dict[str, Any]] = []

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

    async def build(self) -> MIMEMultipart:
        logger.info("Building the email.")
        env = Environment(loader=FileSystemLoader(RESOURCES_DIR))
        template = env.get_template(EmailBuilder._EMAIL_TEMPLATE_NAME)
        context = {
            'night': self._night,
            'telescope_data': self._telescope_data,
        }
        content = template.render(context)

        # Create message
        message = MIMEMultipart("related")
        message["Subject"] = self._subject

        # Attach HTML
        message.attach(MIMEText(content, "html"))
        logger.info("HTML content attached to email.")

        # Attach logo araucaria
        await EmailBuilder._add_logo_to_message(message=message, filename=EmailBuilder._FILENAME_ARAUCARIA_LOGO,
                                                template_name="logo_araucaria")
        # Attach logo camk
        await EmailBuilder._add_logo_to_message(message=message, filename=EmailBuilder._FILENAME_LOGO_CAMK_PAN,
                                                template_name="logo_camk")
        # Attach logo akond
        await EmailBuilder._add_logo_to_message(message=message, filename=EmailBuilder._FILENAME_LOGO_AKOND,
                                                template_name="logo_akond")
        # Attach logo HALina
        await EmailBuilder._add_logo_to_message(message=message, filename=EmailBuilder._FILENAME_LOGO_HALINA,
                                                template_name="logo_halina")
        # Attach logo OCM
        await EmailBuilder._add_logo_to_message(message=message, filename=EmailBuilder._FILENAME_LOGO_OCM,
                                                template_name="logo_ocm")

        return message

    @staticmethod
    async def _add_logo_to_message(message: MIMEMultipart, filename: str, template_name: str):
        async with aiofiles.open(os.path.join(RESOURCES_DIR, filename), 'rb') as logo:
            logo_data = await logo.read()
        logo_image = MIMEImage(logo_data)
        logo_image.add_header('Content-ID', f'<{template_name}>')
        logo_image.add_header('Content-Disposition', 'inline', filename=filename)
        message.attach(logo_image)
        logger.debug(f"Logo {template_name} image attached to email.")
