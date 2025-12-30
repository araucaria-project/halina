import asyncio
import datetime
import logging
import math
from typing import Dict, List, Union, Optional

from astropy.coordinates import get_moon

from configuration import GlobalConfig
from halina.date_utils import DateUtils
from halina.email_rapport.data_collector_classes.fwhm_point import FwhmPoint
from halina.email_rapport.email_builder import EmailBuilder
from halina.email_rapport.email_sender import EmailSender
from halina.email_rapport.telescope_data_collector import TelescopeDtaCollector
from halina.email_rapport.weather_chart_builder import WeatherChartBuilder
from halina.email_rapport.weather_data_collector import WeatherDataCollector
from halina.service_nats_dependent import ServiceNatsDependent
from pyaraucaria.ephemeris import moon_phase
from pyaraucaria.date import get_oca_jd, datetime_to_julian

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailRapportService(ServiceNatsDependent):
    _NAME = "EmailRapportService"

    # time to retry sending email on night. After this night will be skipped.
    # for now is only waiting to connection to NATS
    _SKIPPING_TIME = 1800  # 30 min

    def __init__(self, utc_offset: int = 0, **kwargs):
        super().__init__(**kwargs)
        self._utc_offset: int = utc_offset
        self._telescopes: List[str] = GlobalConfig.get(GlobalConfig.TELESCOPES)
        self._send_at_time = datetime.time(GlobalConfig.get(GlobalConfig.SEND_AT),
                                           GlobalConfig.get(GlobalConfig.SEND_AT_MIN))

    @staticmethod
    def _get_moon_phase(lat: float, lon: float, elev: float) -> str:
        if isinstance(lat, float) and isinstance(lon, float) and isinstance(elev, Union[float, int]):
            _moon_phase = moon_phase(
                date_utc=DateUtils.yesterday_midnight_utc_tz(), latitude=lat, longitude=lon, elevation=elev
            )
            if isinstance(_moon_phase, float):
                return f" Moon phase: {round(_moon_phase)}%"
            else:
                return ''
        else:
            return ''

    @staticmethod
    def _get_oca_jd() -> str:
        return f", OCM night: {math.floor(get_oca_jd(datetime_to_julian(DateUtils.yesterday_midnight_utc())))}"

    @staticmethod
    def _format_night() -> str:
        yesterday_midday = DateUtils.yesterday_local_midday_in_utc()
        today_midday = DateUtils.today_local_midday_in_utc()

        if yesterday_midday.month == today_midday.month:
            return f"{yesterday_midday.day}-{today_midday.day} {yesterday_midday.strftime('%b %Y')}"
        else:
            return (f"{yesterday_midday.day} {yesterday_midday.strftime('%b')} - {today_midday.day} "
                    f"{today_midday.strftime('%b %Y')}")

    async def _main(self) -> None:
        try:
            today_date = datetime.datetime.now(datetime.timezone.utc).date()
            send_at_time = datetime.datetime.combine(today_date, self._send_at_time, tzinfo=datetime.timezone.utc)
            # if we start application after sending time wait until next day
            if send_at_time < datetime.datetime.now(datetime.timezone.utc):
                send_at_time = send_at_time + datetime.timedelta(days=1)
            while True:
                now = datetime.datetime.now(datetime.timezone.utc)
                await asyncio.sleep((send_at_time - now).total_seconds())
                try:
                    start = datetime.datetime.now(datetime.timezone.utc)
                    logger.debug(f"Start sending emails today: {now.date()}")
                    await self._collect_data_and_send()
                    stop = datetime.datetime.now(datetime.timezone.utc)
                    logger.debug(f"Finish sending emails today: {now.date()}")
                    working_time_minutes = (stop - start).total_seconds() / 60
                    logger.info(f"Email sender finish sending message today: {now.date()} . "
                                f"Proces takes {working_time_minutes}")
                except SendEmailException as e:
                    logger.error(f"Email sender service cath error: {e}")

                send_at_time = send_at_time + datetime.timedelta(days=1)

        except asyncio.CancelledError:
            logger.info(f"Email sender service was stopped")
            raise

    async def _on_start(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    async def _collect_data_and_send(self) -> None:
        # Can't waiting infinity to send email from one night because this block other nights
        deadline = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            seconds=EmailRapportService._SKIPPING_TIME)
        # waiting to connection to nats if not already open
        r = await self._wait_to_open_nats(deadline=deadline)
        if not r:
            logger.warning(f"Can not send email rapport because NATS connection is not open")
            raise SendEmailException()
        logger.info(f"Collecting data from telescopes: {self._telescopes}")
        telescopes: Dict[str, TelescopeDtaCollector] = {}
        if self._telescopes:
            for tel in self._telescopes:
                telescopes[tel] = TelescopeDtaCollector(telescope_name=tel, utc_offset=self._utc_offset)

        # weather collector
        wdc = WeatherDataCollector()

        coros = [i.collect_data() for i in telescopes.values()]
        coros.append(wdc.collect_data())
        await asyncio.gather(*coros, return_exceptions=True)

        logger.info(f"Scanning stream for fits completed.")
        for name, i in telescopes.items():
            logger.info(f"Find fits for {name}: {i.count_fits}")

        # Prepare data for email
        telescope_data: List[Dict[str, int]] = []
        fwhm_data: Dict[str, Dict[str, Union[str, List[FwhmPoint]]]] = {}
        for tel in self._telescopes:
            telescope_info = {
                'name': tel,
                'color': telescopes[tel].color,
                'count_fits': telescopes[tel].count_fits,
                'count_fits_processed': telescopes[tel].count_fits_processed,
                'malformed_raw_count': telescopes[tel].malformed_raw_count,
                'malformed_zdf_count': telescopes[tel].malformed_zdf_count,
                'objects': telescopes[tel].objects,
                'fits_group_type': telescopes[tel].fits_group_type
            }
            telescope_data.append(telescope_info)
            fwhm_data[tel] = {'color': telescopes[tel].color, 'fwhm_data': telescopes[tel].fwhm_data}

        # Build and send email
        night = self._format_night()
        _moon_phase = self._get_moon_phase(
            lat=telescopes[self._telescopes[0]].tel_lat,
            lon=telescopes[self._telescopes[0]].tel_lon,
            elev=telescopes[self._telescopes[0]].tel_elev
        )
        email_recipients: List[str] = GlobalConfig.get(GlobalConfig.EMAILS_TO)

        if len(email_recipients) == 0:
            logger.info(f"No recipient specified.")

        # build charts
        wcb = WeatherChartBuilder()
        wcb.set_data_weather(wdc.data_weather)
        wcb.set_data_fwhm(fwhm_data)
        await wcb.build()

        email_builder = (EmailBuilder()
                         .subject(f"Night Report - {night}")
                         .night(night)
                         .oca_jd(self._get_oca_jd())
                         .moon_phase(_moon_phase)
                         .telescope_data(telescope_data)
                         .wind_chart(wcb.get_image_wind_byte())
                         .temperature_chart(wcb.get_image_temperature_byte())
                         .humidity_hart(wcb.get__image_humidity_byte())
                         .pressure_hart(wcb.get_image_pressure_byte())
                         .fwhm_hart(wcb.get_image_fwhm_byte())
                         )

        email_message = await email_builder.build()

        for email in email_recipients:
            email_sender = EmailSender(email)
            result = await email_sender.send(email_message)
            if result:
                logger.info(f"Mail sent successfully to {email}!")
            else:
                logger.error(f"Failed to send mail to {email}.")


class SendEmailException(Exception):
    pass
