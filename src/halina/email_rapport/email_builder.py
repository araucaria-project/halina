"""
Email Builder module.

This module defines the EmailBuilder class which constructs email messages from templates and data.

Classes:
    - EmailBuilder: Builds email messages from templates.
"""

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
    """
    Builds email messages from templates.

    Attributes:
        _subject (str): Subject of the email.
        _night (str): Night information for the email.
        _telescope_data (List[Dict[str, Any]]): Data from telescopes.
        _data_objects (Dict[str, DataObject]): Data objects to include in the email.
        _image_path (str): Path to the image to include in the email.
        _logo_path (str): Path to the logo to include in the email.
    """

    def __init__(self):
        self._subject: str = ""
        self._night: str = ""
        self._telescope_data: List[Dict[str, Any]] = []
        self._data_objects: Dict[str, DataObject] = {}
        self._image_path: str = "src/halina/email_rapport/resources/zdjecie.png"
        self._logo_path: str = "src/halina/email_rapport/resources/araucaria_logo.png"

    def set_subject(self, subject: str) -> None:
        """
        Sets the subject of the email.

        Args:
            subject (str): Subject of the email.
        """
        self._subject = subject

    def subject(self, subject: str) -> 'EmailBuilder':
        """
        Fluent interface for setting the subject of the email.

        Args:
            subject (str): Subject of the email.

        Returns:
            EmailBuilder: Instance of EmailBuilder for method chaining.
        """
        self.set_subject(subject)
        return self

    def set_night(self, night: str) -> None:
        """
        Sets the night information for the email.

        Args:
            night (str): Night information.
        """
        self._night = night
        logger.info(f"Night set to: {night}")

    def night(self, night: str) -> 'EmailBuilder':
        """
        Fluent interface for setting the night information for the email.

        Args:
            night (str): Night information.

        Returns:
            EmailBuilder: Instance of EmailBuilder for method chaining.
        """
        self.set_night(night)
        return self

    def set_telescope_data(self, telescope_data: List[Dict[str, Any]]) -> None:
        """
        Sets the telescope data for the email.

        Args:
            telescope_data (List[Dict[str, Any]]): Data about telescopes.
        """
        self._telescope_data = telescope_data
        logger.info("Telescope data set.")

    def telescope_data(self, telescope_data: List[Dict[str, Any]]) -> 'EmailBuilder':
        """
        Fluent interface for setting the telescope data for the email.

        Args:
            telescope_data (List[Dict[str, Any]]): Data about telescopes.

        Returns:
            EmailBuilder: Instance of EmailBuilder for method chaining.
        """
        self.set_telescope_data(telescope_data)
        return self

    def set_data_objects(self, data_objects: Dict[str, DataObject]) -> None:
        """
        Sets the data objects for the email.

        Args:
            data_objects (Dict[str, DataObject]): Data objects to include in the email.
        """
        self._data_objects = data_objects
        logger.info("Data objects set.")

    def data_objects(self, data_objects: Dict[str, DataObject]) -> 'EmailBuilder':
        """
        Fluent interface for setting the data objects for the email.

        Args:
            data_objects (Dict[str, DataObject]): Data objects to include in the email.

        Returns:
            EmailBuilder: Instance of EmailBuilder for method chaining.
        """
        self.set_data_objects(data_objects)
        return self

    async def build(self) -> MIMEMultipart:
        """
        Builds the email message.

        Returns:
            MIMEMultipart: The constructed email message.
        """
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

        # Attach logo
        async with aiofiles.open(self._logo_path, 'rb') as logo:
            logo_data = await logo.read()
        logo_image = MIMEImage(logo_data)
        logo_image.add_header('Content-ID', '<logo>')
        logo_image.add_header('Content-Disposition', 'inline', filename="araucaria_logo.png")
        message.attach(logo_image)
        logger.info("Logo image attached to email.")

        return message
