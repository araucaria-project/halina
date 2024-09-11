import asyncio
import logging
from typing import Dict
from pyaraucaria.date import datetime_to_julian
from serverish.messenger import get_reader
from halina.asyncio_util_functions import wait_for_psce
from halina.date_utils import DateUtils

logger = logging.getLogger(__name__.rsplit('.')[-1])


class HarvesterFileRapport:
    _NUMBER_STREAMS = 1

    _STR_NAME_DOWNLOAD = 'download'

    def __init__(self, telescope_name: str = "", utc_offset: int = 0, day=None):
        self._telescope_name = telescope_name.strip()
        self._utc_offset: int = utc_offset  # offset hour for time zones
        self._download_stream: str = f"tic.status.{self._telescope_name}.download"

        # {fits_id: dict(raw: raw_fits, zdf: zdf_fits)}
        self._finish_reading_streams: int = 0

        # collected data
        self.downloaded_files: int = 0
        self.malformed_download_count: int = 0
        self.fits_existing_files: Dict[str, int] = {}  # dict witch data to parse to json

    def _get_download_stream(self) -> str:
        return self._download_stream

    def _count_malformed_fits(self, main_key: str):
        if main_key == HarvesterFileRapport._STR_NAME_DOWNLOAD:
            self.malformed_download_count += 1

    async def _read_data_from_download(self):
        stream = self._get_download_stream()
        yesterday_midday = DateUtils.yesterday_local_midday_in_utc()
        today_midday = DateUtils.today_local_midday_in_utc()
        reader = get_reader(stream, deliver_policy='by_start_time', opt_start_time=yesterday_midday)
        try:
            await reader.open()
            while True:
                try:
                    data, meta = await wait_for_psce(reader.read_next(), 2)
                except asyncio.TimeoutError:
                    logger.info(f"Stop waiting for new date in stream - stream is empty. {stream}")
                    break
                logger.debug(f"Data was read from stream {stream}")

                if not HarvesterFileRapport._validate_download(data=data, stream=stream):
                    logger.info("Malformed download")
                    self._count_malformed_fits(HarvesterFileRapport._STR_NAME_DOWNLOAD)
                    continue

                fits_id = data.get("fits_id")
                param = data.get("param")
                obs = param.get("date_obs")
                try:
                    jd = datetime_to_julian(obs)
                except (ValueError, TypeError):
                    logger.info(f"The read record from stream {stream} has wrong format: JD")
                    self._count_malformed_fits(HarvesterFileRapport._STR_NAME_DOWNLOAD)
                    continue
                jd_today_midday = datetime_to_julian(today_midday)
                # if the difference between the beginning of the observation and the date of observation is greater
                # than 1, it means that the day has passed and there is another night
                if (jd_today_midday - jd) >= 1:
                    break
                # --------------------------------------------------------------
                download = data
                if download is not None:
                    self.downloaded_files += 1
                    # 'error_key' is only just for case because stream is evaluate earlier
                    typ = self._map_img_typ_to_typ_name(download.get('param', {}).get('image_type', ''))
                    if typ != 'snap' and typ != 'focus':
                        filename = download.get('param', {}).get('raw_file_name', 'error_key')
                        self.fits_existing_files[filename] = 1
                        logger.debug(f'Read downloaded fits file name; {filename}')
                await asyncio.sleep(0)
        finally:
            self._finish_reading_streams += 1
            await reader.close()

    @staticmethod
    def _validate_download(data: dict, stream: str) -> bool:
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
        filename = param.get('raw_file_name')
        if not filename:
            logger.info(f"The read record from stream {stream} has no field:: raw_file_name")
            return False
        image_type = param.get('image_type')
        if not image_type:
            logger.info(f"The read record from stream {stream} has no field:: image_type")
            return False
        return True

    async def collect_data(self):
        logger.info(f"Start reading data from streams: {self._get_download_stream()}")
        self._finish_reading_streams = 0
        coros = [self._read_data_from_download()]
        await asyncio.gather(*coros, return_exceptions=True)
        logger.info(f"Finished reading data from streams: {self._get_download_stream()}")

    @staticmethod
    def _map_img_typ_to_typ_name(img_typ: str) -> str:
        out = img_typ.lower()
        if out == "focusing":
            out = "focus"
        return out
