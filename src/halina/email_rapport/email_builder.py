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
    _FILENAME_LOGO_AKOND = "logo_akond_compression.png"
    _FILENAME_LOGO_CAMK_PAN = "logo_camk_pan_compression.png"
    _FILENAME_ARAUCARIA_LOGO = "araucaria_logo_compression.png"
    _FILENAME_LOGO_HALINA = "logo_HALina_compression.png"
    _FILENAME_LOGO_OCM = "logo_ENG_granat_wypelniony_srodek_compression.png"
    _EMAIL_TEMPLATE_NAME = "email_template.html"

    def __init__(self):
        self._subject: str = ""
        self._night: str = ""
        self._moon_phase: str = ""
        self._oca_jd: str = ""
        self._telescope_data: List[Dict[str, Any]] = []
        self._wind_chart = None
        self._temperature_chart = None
        self._pressure_hart = None
        self._humidity_hart = None
        self._fwhm_hart = None

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

    def set_moon_phase(self, moon_phase: str) -> None:
        self._moon_phase = moon_phase

    def moon_phase(self, moon_phase: str) -> 'EmailBuilder':
        self.set_moon_phase(moon_phase)
        return self

    def set_oca_jd(self, oca_jd: str) -> None:
        self._oca_jd = oca_jd

    def oca_jd(self, oca_jd: str) -> 'EmailBuilder':
        self.set_oca_jd(oca_jd)
        return self

    def set_telescope_data(self, telescope_data: List[Dict[str, Any]]) -> None:
        self._telescope_data = telescope_data
        logger.info(f"Telescope data set.")

    def telescope_data(self, telescope_data: List[Dict[str, Any]]) -> 'EmailBuilder':
        self.set_telescope_data(telescope_data)
        return self

    def set_wind_chart(self, chart: bytes):
        self._wind_chart = chart

    def wind_chart(self, chart: bytes):
        self.set_wind_chart(chart)
        return self

    def set_temperature_chart(self, chart: bytes):
        self._temperature_chart = chart

    def temperature_chart(self, chart: bytes):
        self.set_temperature_chart(chart)
        return self

    def set_pressure_hart(self, chart: bytes):
        self._pressure_hart = chart

    def pressure_hart(self, chart: bytes):
        self.set_pressure_hart(chart)
        return self

    def set_humidity_hart(self, chart: bytes):
        self._humidity_hart = chart

    def humidity_hart(self, chart: bytes):
        self.set_humidity_hart(chart)
        return self

    def set_fwhm_hart(self, chart: bytes):
        self._fwhm_hart = chart

    def fwhm_hart(self, chart: bytes):
        self.set_fwhm_hart(chart)
        return self

    async def build(self) -> MIMEMultipart:
        logger.info("Building the email.")
        env = Environment(loader=FileSystemLoader(RESOURCES_DIR))
        template = env.get_template(EmailBuilder._EMAIL_TEMPLATE_NAME)
        context = {
            'night': self._night,
            'telescope_data': self._telescope_data,
            'moon_phase': self._moon_phase,
            'oca_jd': self._oca_jd
        }
        content = template.render(context)

        # Create message
        message = MIMEMultipart("related")
        message["Subject"] = self._subject

        # Attach HTML
        message.attach(MIMEText(content, "html"))
        logger.info("HTML content attached to email.")

        logger.info("Weather charts attached to email.")
        # Attach wind chart
        await EmailBuilder._add_chart_to_message(message=message, chart=self._wind_chart,
                                                 chart_name="wind_chart")

        # Attach temperature chart
        await EmailBuilder._add_chart_to_message(message=message, chart=self._temperature_chart,
                                                 chart_name="temperature_chart")

        # Attach humidity chart
        await EmailBuilder._add_chart_to_message(message=message, chart=self._humidity_hart,
                                                 chart_name="humidity_chart")

        # Attach pressure chart
        await EmailBuilder._add_chart_to_message(message=message, chart=self._pressure_hart,
                                                 chart_name="pressure_chart")

        await EmailBuilder._add_chart_to_message(message=message, chart=self._fwhm_hart,
                                                 chart_name="fwhm_chart")

        logger.info("Logos charts attached to email.")
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
        async with aiofiles.open(os.path.join(RESOURCES_DIR, 'pictures', filename), 'rb') as logo:
            logo_data = await logo.read()
        logo_image = MIMEImage(logo_data)
        logo_image.add_header('Content-ID', f'<{template_name}>')
        logo_image.add_header('Content-Disposition', 'inline', filename=filename)
        message.attach(logo_image)
        logger.debug(f"Logo {template_name} image attached to email.")

    @staticmethod
    async def _add_chart_to_message(message: MIMEMultipart, chart: bytes, chart_name: str):
        if chart is None:
            logger.warning(f"Weather chart is None. Char name: {chart_name}")
            return
        try:
            chart_image = MIMEImage(chart)
        except Exception as e:
            logger.error(e)
            raise
        chart_image.add_header('Content-ID', f'{chart_name}')
        chart_image.add_header('Content-Disposition', 'inline', filename=f"{chart_name}.png")
        message.attach(chart_image)
