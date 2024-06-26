import asyncio
import logging
import datetime
from typing import List, Dict
from collections import defaultdict

from serverish.messenger import Messenger

from configuration import GlobalConfig
from halina.email_rapport.email_builder import EmailBuilder
from halina.email_rapport.email_sender import EmailSender
from halina.email_rapport.telescope_data_collector import TelescopeDtaCollector
from halina.service import Service
from halina.email_rapport.data_collector_classes.data_object import DataObject
from halina.date_utils import DateUtils

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailRapportService(Service):

    def __init__(self, utc_offset: int = 0):
        super().__init__()
        self._nats_messenger = Messenger()
        self._utc_offset: int = utc_offset
        self._telescopes: list = GlobalConfig.get(GlobalConfig.TELESCOPES_NAME)

    @staticmethod
    def format_night() -> str:
        yesterday_midday = DateUtils.yesterday_midday()
        today_midday = DateUtils.today_midday()

        if yesterday_midday.month == today_midday.month:
            return f"{yesterday_midday.day}-{today_midday.day} {yesterday_midday.strftime('%b %Y')}"
        else:
            return f"{yesterday_midday.day} {yesterday_midday.strftime('%b')} - {today_midday.day} {today_midday.strftime('%b %Y')}"

    @staticmethod
    def merge_data_objects(objects: Dict[str, DataObject]) -> Dict[str, DataObject]:
        merged_objects = defaultdict(lambda: DataObject(name="", count=0, filters=set()))

        for obj in objects.values():
            if merged_objects[obj.name].name == "":
                merged_objects[obj.name].name = obj.name
            merged_objects[obj.name].count += obj.count
            merged_objects[obj.name].filters.update(obj.filters)

        return merged_objects
    async def _main(self):
        try:
            await self._collect_data_and_send()
        except SendEmailException:
            pass

    async def _on_start(self):
        pass

    async def _on_stop(self):
        pass

    async def _collect_data_and_send(self):
        if not self._nats_messenger.is_open:
            logger.warning(f"Can not send email rapport because NATS connection is not open")
            raise SendEmailException()

        logger.info(f"Collecting data from telescopes: {self._telescopes}")
        telescopes = {}
        if self._telescopes:
            for tel in self._telescopes:
                telescopes[tel] = TelescopeDtaCollector(telescope_name=tel, utc_offset=self._utc_offset)

        coros = [i.collect_data() for i in telescopes.values()]
        await asyncio.gather(*coros, return_exceptions=True)
        logger.info(f"Scanning stream for fits completed. "
                    f"Find fits: {[f"{name}: ({i.count_fits})" for name, i in telescopes.items()]}")

        # Prepare data for email
        telescope_data = []
        all_data_objects = defaultdict(lambda: DataObject(name="", count=0, filters=set()))

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
        night = self.format_night()

        email_builder = EmailBuilder()
        email_builder.subject("Night Report")
        email_builder.night(night)
        email_builder.telescope_data(telescope_data)
        email_builder.data_objects(all_data_objects)

        email_message = await email_builder.build()
        email_sender = EmailSender("d.chmalu@gmail.com")
        result = await email_sender.send(email_message)
        if result:
            logger.info("Mail sent successfully!")
        else:
            logger.error("Failed to send mail.")

    class SendEmailException(Exception):
        pass
