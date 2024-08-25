import asyncio
import logging
from typing import Optional

from serverish.messenger import Messenger
from configuration import GlobalConfig
from halina.asyncio_util_functions import wait_for_psce
from halina.service import Service

logger = logging.getLogger(__name__.rsplit('.')[-1])


class NatsConnectionService(Service):
    _NAME = "NatsConnectionService"

    EVENT_REFRESH_NATS_CONNECTION = "EVENT_REFRESH_NATS_CONNECTION"
    EVENT_NATS_CONNECTION_OPENED = "EVENT_NATS_CONNECTION_OPENED"

    _RETRY_INTERVAL = 2
    _CHECK_CONN_INTERVAL = 30

    def __init__(self):
        super().__init__()
        self.shared_data.get_events().set(NatsConnectionService.EVENT_REFRESH_NATS_CONNECTION, asyncio.Event())
        self.shared_data.get_events().set(NatsConnectionService.EVENT_NATS_CONNECTION_OPENED, asyncio.Event())
        self._nats_messenger = Messenger()
        self._nats_host: str = GlobalConfig.get(GlobalConfig.NATS_HOST)
        self._nats_port: int = GlobalConfig.get(GlobalConfig.NATS_PORT)
        self._nats_con_fut: Optional[asyncio.Future] = None

    async def _main(self):
        while True:
            time_check = False
            try:
                await wait_for_psce(
                    self.shared_data.get_events().wait(NatsConnectionService.EVENT_REFRESH_NATS_CONNECTION),
                    timeout=NatsConnectionService._CHECK_CONN_INTERVAL)
            except asyncio.TimeoutError:
                time_check = True
                pass
            if self._nats_messenger.is_open:
                if not time_check:
                    self.shared_data.get_events().notify(NatsConnectionService.EVENT_NATS_CONNECTION_OPENED)
                continue
            else:
                await self._open_connection()

    async def _on_start(self):
        await self._open_connection()

    async def _on_stop(self):
        logger.info(f"Closing connection to NATS")
        await self._nats_messenger.close()
        if self._nats_messenger.is_open:
            logger.warning(f"Connection to NATS has not been closed")
        await self._stop_nats_con_fut()

    async def _open_connection(self):
        if self._nats_messenger.conn is None:
            logger.info(f"Creating connection to NATS: {self._nats_host}:{self._nats_port}")
            self._t = await self._nats_messenger.open(self._nats_host, self._nats_port, wait=0)

        # connection open immediately
        if self._nats_messenger.is_open:
            logger.info(f"NATS connection opened")
            self.shared_data.get_events().notify(NatsConnectionService.EVENT_NATS_CONNECTION_OPENED)
        else:  # Connecting in background
            if self._nats_con_fut is None or self._nats_con_fut.done():
                # start waiting to background connection
                logger.info(f"Connection to NATS wasn't created. Start opening in background.")
                # first connect
                if self._nats_messenger.opener_task is not None and not self._nats_messenger.opener_task.done():
                    logger.warning("create first connect background")
                    self._nats_con_fut = asyncio.ensure_future(self._nats_con_fut_callback())
                else:  # reconnect
                    logger.warning("create reconnect")
                    self._nats_con_fut = asyncio.ensure_future(self._wait_to_conn())
            else:
                # connection in progress
                logger.debug(f"Connecting to NATS in progress")

    async def _nats_con_fut_callback(self):
        if self._nats_messenger.opener_task is not None:
            # if opener_task is canceled or timeout this future also will be cancelled
            try:
                await self._nats_messenger.opener_task
            except asyncio.CancelledError:
                logger.info(f"NATS Messenger opener_task was cancelled")
                raise
            except asyncio.TimeoutError:
                logger.info(f"NATS Messenger opener_task has timeout")
                raise
            if self._nats_messenger.is_open:
                self.shared_data.get_events().notify(NatsConnectionService.EVENT_NATS_CONNECTION_OPENED)
            self._nats_con_fut = None

    async def _stop_nats_con_fut(self):
        if self._nats_con_fut is not None:
            if not self._nats_con_fut.done():
                self._nats_con_fut.cancel()
                logger.info(f"NATS connection future was canceled")
            self._nats_con_fut = None

    async def _wait_to_conn(self):
        # nothing better can't create for now
        while True:
            logger.debug("Waiting for reconnect to NATS")
            if self._nats_messenger.conn is None:
                return False
            if self._nats_messenger.is_open:
                self.shared_data.get_events().notify(NatsConnectionService.EVENT_NATS_CONNECTION_OPENED)
                return True
            await asyncio.sleep(NatsConnectionService._RETRY_INTERVAL)
