"""
Telescope Data Collector module.

This module defines the TelescopeDtaCollector class which collects data from telescope streams.

Classes:
    - TelescopeDtaCollector: Collects and processes data from telescope streams.
"""

import asyncio
import logging
from typing import Dict, Optional

from pyaraucaria.date import datetime_to_julian
from serverish.messenger import get_reader

from halina.asyncio_util_functions import wait_for_psce
from halina.date_utils import DateUtils
from halina.email_rapport.data_collector_classes.data_object import DataObject

logger = logging.getLogger(__name__.rsplit('.')[-1])


class TelescopeDtaCollector:
    """
    TelescopeDtaCollector collects and processes data from telescope streams.

    Attributes:
        _NUMBER_STREAMS (int): Number of streams to be read.
        _STR_NAME_RAW (str): Name for the raw stream.
        _STR_NAME_ZDF (str): Name for the ZDF stream.
        _STR_NAME_DOWNLOAD (str): Name for the download stream.
        _utc_offset (int): UTC offset for time calculations.
        _download_stream (str): Name of the download stream.
        _raw_stream (str): Name of the raw stream.
        _zdf_stream (str): Name of the ZDF stream.
        _fits_pair (Dict[str, dict]): Dictionary to store FITS pairs.
        _unchecked_ids (set): Set of unchecked IDs.
        _fits_pair_lock (Optional[asyncio.Lock]): Lock for FITS pair operations.
        _fits_pair_condition (Optional[asyncio.Condition]): Condition for FITS pair operations.
        _finish_reading_streams (int): Counter for finished streams.
        objects (Dict[str, DataObject]): Collected data objects.
        count_fits (int): Count of FITS files.
        count_fits_processed (int): Count of processed FITS files.
        malformed_raw_count (int): Count of malformed raw files.
        malformed_zdf_count (int): Count of malformed ZDF files.
        malformed_download_count (int): Count of malformed download files.
    """

    _NUMBER_STREAMS = 3

    _STR_NAME_RAW = "raw"
    _STR_NAME_ZDF = "zdf"
    _STR_NAME_DOWNLOAD = "download"

    def __init__(self, telescope_name: str = "", utc_offset: int = 0):
        """
        Initializes the TelescopeDtaCollector with the telescope name and UTC offset.

        Args:
            telescope_name (str): The name of the telescope.
            utc_offset (int): The UTC offset for time calculations. Defaults to 0.
        """
        self._utc_offset: int = utc_offset
        self._download_stream: str = f"tic.status.{telescope_name.strip()}.download"
        self._raw_stream: str = f"tic.status.{telescope_name.strip()}.fits.pipeline.raw"
        self._zdf_stream: str = f"tic.status.{telescope_name.strip()}.fits.pipeline.zdf"

        # {fits_id: dict(raw: raw_fits, zdf: zdf_fits)}
        self._fits_pair: Dict[str, dict] = {}
        self._unchecked_ids: set = set()
        self._fits_pair_lock: Optional[asyncio.Lock] = None
        self._fits_pair_condition: Optional[asyncio.Condition] = None
        self._finish_reading_streams: int = 0

        self.objects: Dict[str, DataObject] = {}
        self.count_fits: int = 0
        self.count_fits_processed: int = 0
        self.malformed_raw_count: int = 0
        self.malformed_zdf_count: int = 0
        self.malformed_download_count: int = 0

    @property
    def _fp_lock(self) -> asyncio.Lock:
        """
        Initialization of the FITS pair lock.

        Returns:
            asyncio.Lock: The lock for FITS pair operations.
        """
        if self._fits_pair_lock is None:
            self._fits_pair_lock = asyncio.Lock()
        return self._fits_pair_lock

    @property
    def _fp_condition(self) -> asyncio.Condition:
        """
        Initialization of the FITS pair condition.

        Returns:
            asyncio.Condition: The condition for FITS pair operations.
        """
        if self._fits_pair_condition is None:
            self._fits_pair_condition = asyncio.Condition(lock=self._fp_lock)
        return self._fits_pair_condition

    def _get_download_stream(self) -> str:
        """
        Gets the download stream name.

        Returns:
            str: The download stream name.
        """
        return self._download_stream

    def _get_raw_stream(self) -> str:
        """
        Gets the raw stream name.

        Returns:
            str: The raw stream name.
        """
        return self._raw_stream

    def _get_zdf_stream(self) -> str:
        """
        Gets the ZDF stream name.

        Returns:
            str: The ZDF stream name.
        """
        return self._zdf_stream

    def _count_malformed_fits(self, main_key: str):
        """
        Increments the count of malformed FITS files based on the main key.

        Args:
            main_key (str): The key indicating the type of FITS file (raw, zdf, or download).
        """
        if main_key == TelescopeDtaCollector._STR_NAME_RAW:
            self.malformed_raw_count += 1
        if main_key == TelescopeDtaCollector._STR_NAME_ZDF:
            self.malformed_zdf_count += 1
        if main_key == TelescopeDtaCollector._STR_NAME_DOWNLOAD:
            self.malformed_download_count += 1

    async def _read_data_from_download(self):
        """
        Reads data from the download stream.
        """
        stream = self._get_download_stream()
        yesterday_midday = DateUtils.yesterday_midday()
        reader = get_reader(stream, deliver_policy='by_start_time', opt_start_time=yesterday_midday)
        try:
            await reader.open()
            while True:
                try:
                    data, meta = await wait_for_psce(reader.read_next(), 2)
                except asyncio.TimeoutError:
                    logger.info(f"Stop waiting for new date in stream - stream is empty. {stream}")
                    break

                if not TelescopeDtaCollector._validate_download(data=data, stream=stream):
                    logger.info("Malformed download")
                    self._count_malformed_fits(TelescopeDtaCollector._STR_NAME_DOWNLOAD)
                    continue

                fits_id = data.get("fits_id")
                param = data.get("param")
                obs = param.get("date_obs")
                try:
                    jd = datetime_to_julian(obs)
                except (ValueError, TypeError):
                    logger.info(f"The read record from stream {stream} has wrong format: JD")
                    self._count_malformed_fits(TelescopeDtaCollector._STR_NAME_DOWNLOAD)
                    continue
                jd_yesterday_midday = datetime_to_julian(yesterday_midday)
                # if the difference between the beginning of the observation and the date of observation is greater
                # than 1, it means that the day has passed and there is another night
                if (jd - jd_yesterday_midday) >= 1:
                    break
                async with self._fp_condition:
                    if self._fits_pair.get(fits_id, None) is None:
                        self._fits_pair[fits_id] = {}
                    self._fits_pair[fits_id]["download"] = data
                    self._unchecked_ids.add(fits_id)
                    self._fp_condition.notify_all()
                await asyncio.sleep(0)
        finally:
            self._finish_reading_streams += 1
            async with self._fp_condition:
                self._fp_condition.notify_all()
            await reader.close()

    @staticmethod
    def _validate_download(data: dict, stream: str) -> bool:
        """
        Validates the download data.

        Args:
            data (dict): The data to validate.
            stream (str): The name of the stream.

        Returns:
            bool: True if the data is valid, False otherwise.
        """
        fits_id = data.get("fits_id")
        if not fits_id:
            logger.info(f"The read record from stream {stream} has no field:: fits_id")
            return False
        # ---------------------------- check date in param -----------------------------
        param = data.get("param")
        if not param or not isinstance(param, dict):
            logger.info(f"The read record from stream {stream} has no field:: param")
            return False
        obs = param.get("date_obs")
        if not obs:
            logger.info(f"The read record from stream {stream} has no field:: date_obs")
            return False
        return True

    async def _read_data_from_stream(self, stream: str, main_key: str):
        """
        Reads data from the specified stream.

        Args:
            stream (str): The name of the stream.
            main_key (str): The main key indicating the type of FITS file (raw or zdf).
        """
        yesterday_midday = DateUtils.yesterday_midday()
        reader = get_reader(stream, deliver_policy='by_start_time', opt_start_time=yesterday_midday)
        try:
            await reader.open()
            while True:
                # todo jeśłi przez ikreślony czas nie odczytamy wiadomości uznajemy że stream jest pusty.
                #  Takim rozwiązaniem nie możemy ponawiać prób czytania ze streama gdy będą problemy z połączeniem.
                #  Trzeba by edytować serverish jeśłi będzie potrzebny tutaj taki mechanizm.
                try:
                    # we wait for data from the stream for x seconds, if it returns nothing, We recognize
                    # that the stream is empty
                    data, meta = await wait_for_psce(reader.read_next(), 2)
                except asyncio.TimeoutError:
                    logger.info(f"Stop waiting for new date in stream - stream is empty. {stream}")
                    break
                logger.debug(f"Data was read from stream {stream}")
                # validate data
                if not TelescopeDtaCollector._validate_record(data=data, stream=stream, main_key=main_key):
                    self._count_malformed_fits(main_key)
                    continue
                fits_id = data.get("fits_id")
                content = data.get(main_key)
                header = content.get("header")
                try:
                    jd = float(header.get("JD"))
                except (ValueError, TypeError):
                    logger.info(f"The read record from stream {stream} has wrong format: JD")
                    self._count_malformed_fits(main_key)
                    continue
                jd_yesterday_midday = datetime_to_julian(yesterday_midday)
                # if the difference between the beginning of the observation and the date of observation is greater
                # than 1, it means that the day has passed and there is another night
                if (jd - jd_yesterday_midday) >= 1:
                    break
                async with self._fp_condition:
                    if self._fits_pair.get(fits_id, None) is None:
                        self._fits_pair[fits_id] = {}
                    self._fits_pair[fits_id][main_key] = content
                    self._unchecked_ids.add(fits_id)
                    self._fp_condition.notify_all()
                await asyncio.sleep(0)
        finally:
            self._finish_reading_streams += 1
            async with self._fp_condition:
                self._fp_condition.notify_all()
            await reader.close()

    @staticmethod
    def _validate_record(data: dict, stream: str, main_key: str) -> bool:
        """
        Validates the record data.

        Args:
            data (dict): The data to validate.
            stream (str): The name of the stream.
            main_key (str): The main key indicating the type of FITS file (raw or zdf).

        Returns:
            bool: True if the data is valid, False otherwise.
        """
        fits_id = data.get("fits_id")
        if not fits_id:
            logger.info(f"The read record from stream {stream} has no field:: fits_id")
            return False
        content = data.get(main_key)
        if not content or not isinstance(content, dict):
            logger.info(f"The read record from stream {stream} has no field: {main_key}")
            return False
        # ---------------------------- check date in header ----------------------------
        header = content.get("header")
        if not header and not isinstance(header, dict):
            logger.info(f"The read record from stream {stream} has no field:: header")
            return False
        jd = header.get("JD")
        if not jd:
            logger.info(f"The read record from stream {stream} has no field:: JD")
            return False
        return True

    async def collect_data(self):
        """
        Collects data from all streams and evaluates it.
        """
        logger.info(f"Start reading data from streams: {self._get_raw_stream()} & {self._get_zdf_stream()} "
                    f"& {self._get_download_stream()}")
        self._finish_reading_streams = 0
        coros = [self._read_data_from_download(),
                 self._read_data_from_stream(self._get_raw_stream(), TelescopeDtaCollector._STR_NAME_RAW),
                 self._read_data_from_stream(self._get_zdf_stream(), TelescopeDtaCollector._STR_NAME_ZDF),
                 self._evaluate_data()]
        result = await asyncio.gather(*coros, return_exceptions=True)
        logger.info(f"Finished reading data from streams. Read {self.count_fits} record")

    async def _evaluate_data(self):
        """
        Evaluates the collected data and processes FITS pairs.
        """
        async with self._fp_condition:
            while self._finish_reading_streams < TelescopeDtaCollector._NUMBER_STREAMS:
                await self._fp_condition.wait()
                # checking only last added ids - making program faster
                unchecked_ids = self._unchecked_ids
                self._unchecked_ids = set()  # reset ids
                for id_ in unchecked_ids:
                    pair = self._fits_pair.get(id_)  # pair is always !=Null

                    # if dict has _NUMBER_STREAMS key that mean we have all data to process
                    if len(pair) == TelescopeDtaCollector._NUMBER_STREAMS:
                        self._fits_pair.pop(id_)
                        await self._process_pair(pair)
            # process not completed fits pair (pair = raw + zdf)
            for id_, pair in self._fits_pair.items():
                await self._process_pair(pair)
            self._fits_pair = {}  # clear pairs

    async def _process_pair(self, pair: dict):
        """
        Processes a FITS pair.

        Args:
            pair (dict): The FITS pair to process.
        """
        try:
            raw = pair.get(TelescopeDtaCollector._STR_NAME_RAW)
            if not raw:
                # if pair don't have raw photo that mean is no photo
                return
            zdf = pair.get(TelescopeDtaCollector._STR_NAME_ZDF, None)
            if zdf is not None:
                self.count_fits_processed += 1

            objs = raw.get("objects", {})
            filter_ = raw.get("header", {}).get("FILTER", None)
            for k, v in objs.items():
                obj_name = k
                o = self.objects.get(obj_name, None)
                if o is not None:
                    o.count += 1
                    if filter_ is not None:
                        o.filters.add(filter_)  # add filter if not exist
                else:
                    o = DataObject(name=obj_name, count=1)
                    if filter_ is not None:
                        o.filters.add(filter_)
                    self.objects[obj_name] = o

            self.count_fits += 1
        except (KeyboardInterrupt, asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception as e:
            logger.error(f"Error when extracting data from record: {e}")
            self.malformed_raw_count += 1
