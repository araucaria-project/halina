import asyncio
import datetime
import logging
from typing import List, Optional

from serverish.messenger import get_reader

from halina.asyncio_util_functions import wait_for_psce
from halina.date_utils import DateUtils
from halina.email_rapport.data_collector_classes.weather_point import WeatherPoint

logger = logging.getLogger(__name__.rsplit('.')[-1])


class WeatherDataCollector:

    def __init__(self, utc_offset: int = 0):
        self._utc_offset: int = utc_offset  # offset hour for time zones
        self._measurements_stream: str = f"telemetry.weather.davis"

        self._finish_reading_measurements_stream: bool = True

        # collected data
        self._malformed_record_measurements: int = 0
        self.data_weather: List[WeatherPoint] = []

    async def collect_data(self):
        logger.info(f"Start reading data from stream: {self._measurements_stream}")
        self._finish_reading_measurements_stream = False
        coros = [self._read_data_from_measurements_stream()]
        await asyncio.gather(*coros, return_exceptions=True)
        logger.info(f"Finished reading data from stream {self._measurements_stream}")

    async def _read_data_from_measurements_stream(self):
        stream = self._measurements_stream
        yesterday_midday = DateUtils.yesterday_local_midday_in_utc()
        today_midday = DateUtils.today_local_midday_in_utc()
        reader = get_reader(stream, deliver_policy='by_start_time', opt_start_time=yesterday_midday)
        try:
            await reader.open()
            while True:
                try:
                    # we wait for data from the stream for x seconds, if it returns nothing, We recognize
                    # that the stream is empty
                    data, meta = await wait_for_psce(reader.read_next(), 2)
                except asyncio.TimeoutError:
                    logger.info(f"Stop waiting for new date in stream - stream is empty. {stream}")
                    break
                logger.debug(f"Data was read from stream {stream}")
                # validate data
                if not WeatherDataCollector._validate_record(data=data, stream=stream):
                    logger.debug(f"Record from {stream} is malformed")
                    self._malformed_record_measurements += 1
                    continue
                # check time
                ts = data.get("ts")
                ts_dt = datetime.datetime(*ts)
                if ts_dt > today_midday:
                    break

                # read data
                measurement: dict = data.get('measurements', {})

                # hour = ts_dt.hour + ts_dt.minute / 60 + ts_dt.second / 3600
                wind = measurement.get('wind_10min_ms')
                temperature = measurement.get('temperature_C')
                humidity = measurement.get('humidity')
                wind_dir_deg = measurement.get('wind_dir_deg')
                pressure = measurement.get('pressure_Pa')
                logger.debug(f"Read weather point : hour: {ts_dt} wind: {wind} temperature:{temperature} "
                             f"humidity:{humidity} wind_dir_deg:{wind_dir_deg} pressure:{pressure}")
                self.data_weather.append(WeatherPoint(date=ts_dt, temperature=temperature, humidity=humidity, wind=wind,
                                                      wind_dir_deg=wind_dir_deg, pressure=pressure))

                await asyncio.sleep(0)
        finally:
            self._finish_reading_measurements_stream = True
            await reader.close()

    @staticmethod
    def _validate_record(data: dict, stream: str) -> bool:
        if not data:
            return False
        # validate timestamp
        ts: Optional[list] = data.get('ts', None)
        if ts is None:
            return False
        try:
            datetime.datetime(*ts)
        except TypeError:
            return False
        # validate weather
        measurements = data.get('measurements', {})
        if not isinstance(measurements, dict):
            logger.info(f"The read record from stream {stream} has damaged field measurements. Value: {measurements}")
            return False
        wind = measurements.get('wind_10min_ms')
        temperature = measurements.get('temperature_C')
        humidity = measurements.get('humidity')
        wind_dir_deg = measurements.get('wind_dir_deg')
        pressure = measurements.get('pressure_Pa')
        if not isinstance(wind, float) and not isinstance(wind, int):
            logger.info(f"The read record from stream {stream} has damaged field wind. Value: {wind}")
            return False
        if not isinstance(temperature, float) and not isinstance(temperature, int):
            logger.info(f"The read record from stream {stream} has damaged field temperature. Value: {temperature}")
            return False
        if not isinstance(humidity, float) and not isinstance(humidity, int):
            logger.info(f"The read record from stream {stream} has damaged field wind. Value: {wind}")
            return False
        if not isinstance(wind_dir_deg, float) and not isinstance(wind_dir_deg, int):
            logger.info(f"The read record from stream {stream} has damaged field wind_dir_deg. Value: {wind_dir_deg}")
            return False
        if not isinstance(pressure, float) and not isinstance(pressure, int):
            logger.info(f"The read record from stream {stream} has damaged field pressure. Value: {pressure}")
            return False
        return True
