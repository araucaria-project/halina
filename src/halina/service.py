import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__.rsplit('.')[-1])

# todo jak będzie potem dóżo serwisów to można uruchomić każdy w thread i by było "1 serwis = 1 thread i" w każdym
#  osobna pętla asyncio


class Service(ABC):

    _NAME = "Default"

    def __init__(self):
        self._main_task: Optional[asyncio.Task] = None

    @abstractmethod
    async def _main(self):
        pass

    @abstractmethod
    async def _on_start(self):
        pass

    @abstractmethod
    async def _on_stop(self):
        pass

    async def start(self):
        if self._main_task is None or self._main_task.done():
            logger.debug(f"Start service {self._NAME}")
            await self._on_start()
            self._main_task = asyncio.get_running_loop().create_task(self._main())
        else:
            logger.error(f"Can not start service {self._NAME}, because is already running")

    async def stop(self):
        logger.debug(f"Stop service {self._NAME}")
        if self._main_task is not None:
            await self._on_stop()
            self._main_task.cancel()
            try:
                await asyncio.wait(self._main_task)
            except asyncio.CancelledError:
                logger.info(f"Service {self._NAME} was stopped")

    async def join(self):
        try:
            await asyncio.wait([self._main_task])
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            raise
