import logging
from jinja2 import Environment, FileSystemLoader
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import aiofiles
from typing import List, Dict, Any, Union
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
        self._power_chart = None
        self._quality_qmap_chart = None
        self._phot_zero_chart = None
        self._data_files = None

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

    def set_quality_qmap_chart(self, chart: bytes):
        self._quality_qmap_chart = chart

    def quality_qmap_chart(self, chart: bytes):
        self.set_quality_qmap_chart(chart)
        return self

    def set_phot_zero_chart(self, chart: bytes):
        self._phot_zero_chart = chart

    def phot_zero_chart(self, chart: bytes):
        self.set_phot_zero_chart(chart)
        return self

    def set_power_chart(self, chart: bytes):
        self._power_chart = chart

    def power_chart(self, chart: bytes):
        self.set_power_chart(chart)
        return self

    def set_data_files(self, data_files: Dict[str, Union[Dict, List]]):
        self._data_files = data_files

    def data_files(self, data_files: Dict[str, Union[Dict, List]]):
        self.set_data_files(data_files)
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

        await EmailBuilder._add_chart_to_message(message=message, chart=self._quality_qmap_chart,
                                                 chart_name="quality_qmap_chart")

        await EmailBuilder._add_chart_to_message(message=message, chart=self._phot_zero_chart,
                                                 chart_name="phot_zero_chart")

        await EmailBuilder._add_chart_to_message(message=message, chart=self._power_chart,
                                                 chart_name="power_chart")

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

        # Attach files data
        if self._data_files is not None:
            for file_name, file_data in self._data_files.items():
                await EmailBuilder._add_file_to_message(
                    message=message,
                    file_data=file_data,
                    file_name=file_name,
                )

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

    @staticmethod
    async def _add_file_to_message(message: MIMEMultipart, file_data: Union[Dict, List], file_name: str):
        logger.info(f"Starting to create {file_name} 1")
        if file_data is None:
            logger.warning(f"File content is None. File name: {file_name}")
            return
        logger.info(f"Starting to create {file_name} 2")
        if isinstance(file_data, list):
            records_text = "\n".join(
                str(x) if x is not None else "NULL"
                for x in file_data
            )
        else:
            raise NotImplementedError
        logger.info(f"Starting to create {file_name} 3")
        records_text = "AAA\nBBB"

        part = MIMEText(records_text, "plain", "utf-8")
        logger.info(f"Starting to create {file_name} 4")
        part.add_header("Content-Disposition", "attachment", filename=file_name)
        logger.info(f"Starting to create {file_name} 5")
        message.attach(part)
        logger.info(f"Starting to create {file_name} 6")
        logger.debug(f"File {file_name} attached to email.")
