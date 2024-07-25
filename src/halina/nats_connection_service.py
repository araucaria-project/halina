"""
NATS Connection Service module.

This module defines the NatsConnectionService class which manages the connection to a NATS server.

Classes:
    - NatsConnectionService: Manages connection to NATS server.
"""

import logging
from typing import Optional

from serverish.messenger import Messenger
from configuration import GlobalConfig
from halina.service import Service

logger = logging.getLogger(__name__.rsplit('.')[-1])


class NatsConnectionService(Service):
    """
    Manages connection to NATS server.

    Attributes:
        _nats_messenger (Messenger): Messenger instance for NATS communication.
        _nats_host (str): Hostname for NATS server.
        _nats_port (int): Port number for NATS server.
    """

    def __init__(self):
        """
        Initializes the NatsConnectionService.
        """
        super().__init__()
        self._nats_messenger = Messenger()
        self._nats_host: str = GlobalConfig.get(GlobalConfig.NATS_HOST)
        self._nats_port: int = GlobalConfig.get(GlobalConfig.NATS_PORT)

    async def _main(self):
        """
        Main coroutine for the NatsConnectionService.
        """
        pass

    async def _on_start(self):
        """
        Actions to perform on service start.
        """
        logger.info(f"Creating connection to NATS: {self._nats_host}:{self._nats_port}")
        await self._nats_messenger.open(self._nats_host, self._nats_port, wait=5)
        if not self._nats_messenger.is_open:
            logger.warning("Connection to NATS wasn't created")

    async def _on_stop(self):
        """
        Actions to perform on service stop.
        """
        if self._nats_messenger.is_open:
            logger.debug("Closing connection to NATS")
            await self._nats_messenger.close()
        if self._nats_messenger.is_open:
            logger.warning("Connection to NATS has not been closed")
        pass
