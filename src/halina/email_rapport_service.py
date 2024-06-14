import asyncio
import logging

from serverish.messenger import Messenger

from configuration import GlobalConfig
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


class SendEmailException(Exception):
    pass
