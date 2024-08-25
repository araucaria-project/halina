import asyncio
import datetime
import logging
from typing import Dict, List
from collections import defaultdict

from serverish.messenger import Messenger

from configuration import GlobalConfig
from halina.asyncio_util_functions import wait_for_psce
from halina.email_rapport.email_builder import EmailBuilder
from halina.email_rapport.email_sender import EmailSender
from halina.email_rapport.telescope_data_collector import TelescopeDtaCollector
from halina.nats_connection_service import NatsConnectionService
from halina.service import Service
from halina.email_rapport.data_collector_classes.data_object import DataObject
from halina.date_utils import DateUtils

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailRapportService(Service):
    _NAME = "EmailRapportService"

    # time to retry sending email on night. After this night will be skipped.
    # for now is only waiting to connection to NATS
    _SKIPPING_TIME = 1800  # 30 min

    def __init__(self, utc_offset: int = 0):
        super().__init__()
        self._nats_messenger = Messenger()
        self._utc_offset: int = utc_offset
        self._telescopes: List[str] = GlobalConfig.get(GlobalConfig.TELESCOPES)
        self._send_at_time = datetime.time(GlobalConfig.get(GlobalConfig.SEND_AT), 0)

    @staticmethod
    def _format_night() -> str:
        yesterday_midday = DateUtils.yesterday_midday()
        today_midday = DateUtils.today_midday()

        if yesterday_midday.month == today_midday.month:
            return f"{yesterday_midday.day}-{today_midday.day} {yesterday_midday.strftime('%b %Y')}"
        else:
            return f"{yesterday_midday.day} {yesterday_midday.strftime('%b')} - {today_midday.day} {today_midday.strftime('%b %Y')}"

    @staticmethod
    def merge_data_objects(objects: Dict[str, DataObject]) -> Dict[str, DataObject]:
        merged_objects: Dict[str, DataObject] = defaultdict(lambda: DataObject(name="", count=0, filters=set()))

        for obj in objects.values():
            if merged_objects[obj.name].name == "":
                merged_objects[obj.name].name = obj.name
            merged_objects[obj.name].count += obj.count
            merged_objects[obj.name].filters.update(obj.filters)

        return merged_objects

    async def _main(self) -> None:
        try:
            today_date = datetime.datetime.now(datetime.UTC).date()
            send_at_time = datetime.datetime.combine(today_date, self._send_at_time, tzinfo=datetime.UTC)

            # if we start application after sending time wait until next day
            if send_at_time < datetime.datetime.now(datetime.UTC):
                send_at_time = send_at_time + datetime.timedelta(days=1)

            while True:
                now = datetime.datetime.now(datetime.UTC)
                await asyncio.sleep((send_at_time - now).total_seconds())
                try:
                    start = datetime.datetime.now(datetime.UTC)
                    logger.debug(f"Start sending emails today: {now.date()}")
                    await self._collect_data_and_send()
                    stop = datetime.datetime.now(datetime.UTC)
                    logger.debug(f"Finish sending emails today: {now.date()}")
                    working_time_minutes = (stop - start).total_seconds() / 60
                    logger.info(f"Email sender finish sending message today: {now.date()} . "
                                f"Proses takes {working_time_minutes}")
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

    async def _wait_to_open_nats(self, deadline: datetime.datetime) -> bool:
        if self._nats_messenger.is_open:
            return True
        if not self.shared_data.get_events().is_exist(
                NatsConnectionService.EVENT_REFRESH_NATS_CONNECTION) or not self.shared_data.get_events().is_exist(
                NatsConnectionService.EVENT_NATS_CONNECTION_OPENED):
            return False
        self.shared_data.get_events().notify(NatsConnectionService.EVENT_REFRESH_NATS_CONNECTION)
        time = (deadline-datetime.datetime.now(datetime.UTC)).total_seconds()
        try:
            await wait_for_psce(
                self.shared_data.get_events().wait(NatsConnectionService.EVENT_NATS_CONNECTION_OPENED),
                timeout=time)
        except asyncio.TimeoutError:
            pass
        return self._nats_messenger.is_open

    async def _collect_data_and_send(self) -> None:
        # Can't waiting infinity to send email from one night because this block other nights
        deadline = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=EmailRapportService._SKIPPING_TIME)
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

        coros = [i.collect_data() for i in telescopes.values()]
        await asyncio.gather(*coros, return_exceptions=True)

        logger.info(f"Scanning stream for fits completed.")
        for name, i in telescopes.items():
            logger.info(f"Find fits for {name}: {i.count_fits}")

        # Prepare data for email
        telescope_data: List[Dict[str, int]] = []
        all_data_objects: Dict[str, DataObject] = defaultdict(lambda: DataObject(name="", count=0, filters=set()))

        for tel in self._telescopes:
            telescope_info = {
                'name': tel,
                'count_fits': telescopes[tel].count_fits,
                'count_fits_processed': telescopes[tel].count_fits_processed,
                'malformed_raw_count': telescopes[tel].malformed_raw_count,
                'malformed_zdf_count': telescopes[tel].malformed_zdf_count
            }
            telescope_data.append(telescope_info)
            merged_objects = self.merge_data_objects(telescopes[tel].objects)
            for key, value in merged_objects.items():
                all_data_objects[key].name = value.name
                all_data_objects[key].count += value.count
                all_data_objects[key].filters.update(value.filters)

        # Build and send email
        night = self._format_night()
        email_recipients: List[str] = GlobalConfig.get(GlobalConfig.EMAILS_TO)

        if len(email_recipients) == 0:
            logger.info(f"No recipient specified.")

        for email in email_recipients:
            email_builder = (EmailBuilder()
                             .subject(f"Night Report - {night}")
                             .night(night)
                             .telescope_data(telescope_data)
                             .data_objects(all_data_objects))

            email_message = await email_builder.build()

            email_sender = EmailSender(email)
            result = await email_sender.send(email_message)
            if result:
                logger.info(f"Mail sent successfully to {email}!")
            else:
                logger.error(f"Failed to send mail to {email}.")


class SendEmailException(Exception):
    pass
