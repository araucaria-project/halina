import asyncio
import datetime
from abc import ABC

from serverish.messenger import Messenger

from halina.asyncio_util_functions import wait_for_psce
from halina.nats_connection_service import NatsConnectionService
from halina.service import Service


class ServiceNatsDependent(Service, ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._nats_messenger = Messenger()

    async def _wait_to_open_nats(self, deadline: datetime.datetime) -> bool:
        if self._nats_messenger.is_open:
            return True
        if not self.shared_data.get_events().is_exist(
                NatsConnectionService.EVENT_REFRESH_NATS_CONNECTION) or not self.shared_data.get_events().is_exist(
                NatsConnectionService.EVENT_NATS_CONNECTION_OPENED):
            return False
        self.shared_data.get_events().notify(NatsConnectionService.EVENT_REFRESH_NATS_CONNECTION)
        time = (deadline - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        try:
            await wait_for_psce(
                self.shared_data.get_events().wait(NatsConnectionService.EVENT_NATS_CONNECTION_OPENED),
                timeout=time)
        except asyncio.TimeoutError:
            pass
        return self._nats_messenger.is_open
