import asyncio
import logging

from serverish.messenger import Messenger

from configuration import GlobalConfig
from halina.email_rapport.email_builder import EmailBuilder
from halina.email_rapport.email_sender import EmailSender
from halina.email_rapport.telescope_data_collector import TelescopeDtaCollector
from halina.service import Service

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailRapportService(Service):

    def __init__(self, utc_offset: int = 0):
        super().__init__()
        self._nats_messenger = Messenger()
        self._utc_offset: int = utc_offset
        self._telescopes: list = GlobalConfig.get(GlobalConfig.TELESCOPES_NAME)

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

        # todo continue here
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
        total_fits = sum(tel.count_fits for tel in telescopes.values())
        total_fits_processed = sum(tel.count_fits_processed for tel in telescopes.values())
        total_malformed_raw = sum(tel.malformed_raw_count for tel in telescopes.values())
        total_malformed_zdf = sum(tel.malformed_zdf_count for tel in telescopes.values())
        email_data = {
            tel: {
                'count_fits': tel_data.count_fits,
                'count_fits_processed': tel_data.count_fits_processed,
                'malformed_raw_count': tel_data.malformed_raw_count,
                'malformed_zdf_count': tel_data.malformed_zdf_count,
                'objects': tel_data.objects
            } for tel, tel_data in telescopes.items()
        }

        # Build and send email
        email_builder = EmailBuilder()
        email_builder.subject("Night Report")
        email_builder.night("12-14 Dec 2024")
        email_builder.count_fits(total_fits)
        email_builder.count_fits_processed(total_fits_processed)
        email_builder.malformed_raw_count(total_malformed_raw)
        email_builder.malformed_zdf_count(total_malformed_zdf)
        email_builder.telescopes_data(email_data)

        email_message = await email_builder.build()
        email_sender = EmailSender("d.chmalu@gmail.com")
        result = await email_sender.send(email_message)
        if result:
            logger.info("Mail sent successfully!")
        else:
            logger.error("Failed to send mail.")


class SendEmailException(Exception):
    pass
