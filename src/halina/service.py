"""
Service module.

This module defines the base Service class which provides an abstract base for other services
to implement asynchronous start, stop, and main methods.

Classes:
    - Service: Abstract base class for creating services.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__.rsplit('.')[-1])

# todo jak będzie potem dóżo serwisów to można uruchomić każdy w thread i by było "1 serwis = 1 thread i" w każdym
#  osobna pętla asyncio


class Service(ABC):
    """
    Base class for creating services.

    Attributes:
        _main_task (Optional[asyncio.Task]): Main task of the service.
    """

    _NAME = "Default"

    def __init__(self):
        self._main_task: Optional[asyncio.Task] = None

    @abstractmethod
    async def _main(self):
        """
        Main method to be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def _on_start(self):
        """
        Method to be implemented by subclasses to handle actions on service start.
        """
        pass

    @abstractmethod
    async def _on_stop(self):
        """
        Method to be implemented by subclasses to handle actions on service stop.
        """
        pass

    async def start(self):
        """
        Starts the service by creating and running the main task.
        """
        if self._main_task is None or self._main_task.done():
            logger.debug(f"Start service {self._NAME}")
            await self._on_start()
            self._main_task = asyncio.get_running_loop().create_task(self._main())
        else:
            logger.error(f"Cannot start service {self._NAME}, because it is already running")

    async def stop(self):
        """
        Stops the service by canceling the main task and handling cleanup.
        """
        logger.debug(f"Stop service {self._NAME}")
        if self._main_task is not None:
            await self._on_stop()
            self._main_task.cancel()
            try:
                await asyncio.wait([self._main_task])
            except asyncio.CancelledError:
                logger.info(f"Service {self._NAME} was stopped")

    async def join(self):
        """
        Waits for the main task to complete.
        """
        if self._main_task is not None:
            try:
                await asyncio.gather(self._main_task, return_exceptions=True)
            except asyncio.CancelledError:
                logger.info(f"Service {self._NAME} was canceled")
                pass
            except KeyboardInterrupt:
                logger.info(f"Service {self._NAME} was stopped by KeyboardInterrupt")
                raise
