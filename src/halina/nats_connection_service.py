import logging
from typing import Optional

from serverish.messenger import Messenger

from configuration import GlobalConfig
from halina.service import Service

logger = logging.getLogger(__name__.rsplit('.')[-1])


class NatsConnectionService(Service):

    def __init__(self):
        super().__init__()
        self._nats_messenger = Messenger()
        self._nats_host: str = GlobalConfig.get(GlobalConfig.NATS_HOST)
        self._nats_port: int = GlobalConfig.get(GlobalConfig.NATS_PORT)

    async def _main(self):
        pass

    async def _on_start(self):
        logger.info(f"Creating connection to NATS: {self._nats_host}:{self._nats_port}")
        await self._nats_messenger.open(self._nats_host, self._nats_port, wait=5)
        if not self._nats_messenger.is_open:
            logger.warning(f"Connection to NATS wasn't created")

    async def _on_stop(self):
        if self._nats_messenger.is_open:
            logger.debug(f"Closing connection to NATS")
            await self._nats_messenger.close()
        if self._nats_messenger.is_open:
            logger.warning(f"Connection to NATS has not been closed")
        pass
