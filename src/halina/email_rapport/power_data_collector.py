import asyncio
import datetime
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Union, Callable

from halina.email_rapport.data_collector_classes.power_point import PowerPoint
from serverish.messenger import get_reader
from serverish.base.datetime import dt_from_array

from halina.asyncio_util_functions import wait_for_psce
from halina.date_utils import DateUtils

from configuration import GlobalConfig


logger = logging.getLogger(__name__.rsplit('.')[-1])


class PowerDataCollector:

    def __init__(self):
        self._nats_subject: str = "telemetry.power.data-manager"
        self._finish_reading_measurements_stream: bool = True
        self._malformed_record_measurements: int = 0
        self.data_points: List[PowerPoint] = []
        super().__init__()

    async def add_data_point(self, data) -> None:

        ts = data.get("ts")
        ts_dt = dt_from_array(t=ts)
        measurement: dict = data.get('measurements', {})
        state_of_charge = measurement.get('state_of_charge')
        pv_power = measurement.get('pv_power')
        battery_charge = measurement.get('battery_charge')
        battery_discharge = measurement.get('battery_discharge')

        self.data_points.append(PowerPoint(
            date=ts_dt,
            state_of_charge=state_of_charge,
            pv_power=pv_power,
            battery_charge=battery_charge,
            battery_discharge=battery_discharge,
        ))

    async def _validate_record_data(self, data: dict) -> bool:

        measurements = data.get('measurements', {})
        if not isinstance(measurements, dict):
            logger.info(
                f"The read record from stream {self._nats_subject} has damaged field measurements."
                f" Value: {measurements}"
            )
            return False
        state_of_charge = measurements.get('state_of_charge')
        pv_power = measurements.get('pv_power')
        battery_charge = measurements.get('battery_charge')
        battery_discharge = measurements.get('battery_discharge')
        if not isinstance(state_of_charge, float) and not isinstance(state_of_charge, int):
            logger.info(
                f"The read record from subject {self._nats_subject} has damaged field wind. Value: {state_of_charge}"
            )
            return False
        if not isinstance(pv_power, float) and not isinstance(pv_power, int):
            logger.info(
                f"The read record from subject {self._nats_subject} has damaged field temperature. Value: {pv_power}"
            )
            return False
        if not isinstance(battery_charge, float) and not isinstance(battery_charge, int):
            logger.info(
                f"The read record from subject {self._nats_subject} has damaged field wind. Value: {battery_charge}"
            )
            return False
        if not isinstance(battery_discharge, float) and not isinstance(battery_discharge, int):
            logger.info(
                f"The read record from subject {self._nats_subject} has damaged field wind_dir_deg."
                f" Value: {battery_discharge}"
            )
            return False
        return True

    async def collect(self) -> None:
        offset_hours = GlobalConfig.get(GlobalConfig.CHARTS_UTC_OFFSET_HOURS)
        yesterday_midday = DateUtils.yesterday_midday_utc_tz() + datetime.timedelta(hours=offset_hours)
        today_midday = DateUtils.today_midday_utc_tz() + datetime.timedelta(hours=offset_hours)
        reader = get_reader(
            self._nats_subject, deliver_policy='by_start_time', opt_start_time=yesterday_midday, nowait=True
        )
        try:
            async for data, meta in reader:

                if not await self._validate_record(data=data):
                    logger.debug(f"Record from {self._nats_subject} is malformed")
                    self._malformed_record_measurements += 1
                    continue

                # check ts
                ts = data.get("ts")
                ts_dt = dt_from_array(t=ts)
                if ts_dt > today_midday:
                    break
                await self.add_data_point(data=data)
                await asyncio.sleep(0)

        finally:
            logger.info(f'Power data records: {len(self.data_points)}')
            self._finish_reading_measurements_stream = True
            await reader.close()

    async def _validate_record(self, data: dict) -> bool:
        if not data:
            return False
        ts: Optional[list] = data.get('ts', None)
        if ts is None:
            return False
        try:
            datetime.datetime(*ts)
        except TypeError:
            return False
        return await self._validate_record_data(data=data)

    async def collect_data(self):
        logger.info(f"Start reading power data")
        coro = [self.collect()]
        await asyncio.gather(*coro, return_exceptions=True)
        logger.info(f"Finished reading power data")
