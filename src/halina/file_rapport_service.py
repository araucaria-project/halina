import asyncio
import datetime
import logging
from typing import List, Dict

from pyaraucaria.date import get_oca_jd, datetime_to_julian
from serverish.messenger import Messenger

from configuration import GlobalConfig
from halina.asyncio_util_functions import wait_for_psce
from halina.date_utils import DateUtils
from halina.file_raport.file_rapport_creator import FileRapportCreator
from halina.file_raport.harvester_file_rapport import HarvesterFileRapport
from halina.nats_connection_service import NatsConnectionService
from halina.service_nats_dependent import ServiceNatsDependent

logger = logging.getLogger(__name__.rsplit('.')[-1])


class FileRapportService(ServiceNatsDependent):
    _NAME = "FileRapportService"

    # time to retry sending email on night. After this night will be skipped.
    # for now is only waiting to connection to NATS
    _SKIPPING_TIME = 1800  # 30 min

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._send_at_time = datetime.time(GlobalConfig.get(GlobalConfig.SEND_AT),
                                           GlobalConfig.get(GlobalConfig.SEND_AT_MIN))
        self._nats_messenger = Messenger()
        self._telescopes: List[str] = GlobalConfig.get(GlobalConfig.TELESCOPES)

    async def _main(self):
        try:
            today_date = datetime.datetime.now(datetime.timezone.utc).date()
            send_at_time = datetime.datetime.combine(today_date, self._send_at_time, tzinfo=datetime.timezone.utc)
            # if we start application after sending time wait until next day
            if send_at_time < datetime.datetime.now(datetime.timezone.utc):
                send_at_time = send_at_time + datetime.timedelta(days=1)
            while True:
                now = datetime.datetime.now(datetime.timezone.utc)
                await asyncio.sleep((send_at_time - now).total_seconds())

                try:
                    start = datetime.datetime.now(datetime.timezone.utc)
                    logger.debug(f"Start creating file rapport today: {now.date()}")
                    await self._collect_data_and_save()
                    stop = datetime.datetime.now(datetime.timezone.utc)
                    logger.debug(f"Finish creating file rapport today: {now.date()}")
                    working_time_minutes = (stop - start).total_seconds() / 60
                    logger.info(f"File rapport created today: {now.date()} . "
                                f"Proses takes {working_time_minutes}")
                except SaveFileException as e:
                    logger.error(f"Email sender service cath error: {e}")

                send_at_time = send_at_time + datetime.timedelta(days=1)

        except asyncio.CancelledError:
            logger.info(f"Email sender service was stopped")
            raise

    async def _on_start(self):
        pass

    async def _on_stop(self):
        pass

    async def _collect_data_and_save(self):
        # Can't waiting infinity to send email from one night because this block other nights
        deadline = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            seconds=FileRapportService._SKIPPING_TIME)
        # waiting to connection to nats if not already open
        r = await self._wait_to_open_nats(deadline=deadline)
        if not r:
            logger.warning(f"Can not send email rapport because NATS connection is not open")
            raise SaveFileException()
        logger.info(f"Collecting data from telescopes: {self._telescopes}")
        telescopes: Dict[str, HarvesterFileRapport] = {}
        if self._telescopes:
            for tel in self._telescopes:
                telescopes[tel] = HarvesterFileRapport(telescope_name=tel, utc_offset=0)

        coros = [i.collect_data() for i in telescopes.values()]
        await asyncio.gather(*coros, return_exceptions=True)
        logger.info(f"Scanning stream for fits completed.")

        # save read fits filenames to json file
        try:
            await wait_for_psce(self._save_found_fits_to_file(telescopes=telescopes), timeout=240)
        except asyncio.TimeoutError:
            logger.warning(f"Stop waiting for save fits to json file")

    async def _save_found_fits_to_file(self, telescopes: Dict[str, HarvesterFileRapport]):
        to_save = []
        for tel in self._telescopes:
            fc = FileRapportCreator()
            fc.set_data(telescopes[tel].fits_existing_files)
            fc.set_subdir(tel)
            jd = get_oca_jd(datetime_to_julian(DateUtils.yesterday_midnight_utc()))
            fc.set_filename('{:04d}.json'.format(int(jd)))
            to_save.append(fc.save())
        result = await asyncio.gather(*to_save, return_exceptions=True)
        for i in result:
            if i is True:
                logger.debug(f'JSON file saved successfully')
            else:
                logger.warning(f'Can not save JSON file')


class SaveFileException(Exception):
    pass
