import datetime
import logging
import warnings
from astropy.utils import iers
from astropy.utils.exceptions import AstropyWarning
from pyaraucaria.ephemeris import calculate_sun_rise_set

from configuration import GlobalConfig

logger = logging.getLogger(__name__.rsplit('.')[-1])


class DateUtils:
    warnings.simplefilter('ignore', category=AstropyWarning)
    iers.conf.auto_download = False

    @staticmethod
    def today_midday_utc() -> datetime.datetime:
        t = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        t = t.replace(hour=12, minute=0, second=0, microsecond=0)  # set yesterday at middle of the day
        return t

    @staticmethod
    def yesterday_midday_utc() -> datetime.datetime:
        yesterday = DateUtils.today_midday_utc() - datetime.timedelta(days=1)
        return yesterday

    @staticmethod
    def yesterday_midnight_utc() -> datetime.datetime:
        midnight = DateUtils.today_midday_utc() - datetime.timedelta(hours=12)
        return midnight

    @staticmethod
    def today_local_midday_in_utc() -> datetime.datetime:
        """
        Thus method returns the utc equivalent of local time 12 today. E.g. chile local 12 is in utc 16 and method
        return 16

        :return: the utc equivalent of local time 12 today
        """
        t = DateUtils.today_midday_utc()
        # normally timezone is added, but we have to back to utc from current time, so we subtract this
        # e.g. we need chile 12 so utc is 16
        t = t - datetime.timedelta(hours=GlobalConfig.get(GlobalConfig.OBSERVATORY_TIMEZONE, 0))
        return t

    @staticmethod
    def yesterday_local_midday_in_utc() -> datetime.datetime:
        """
        Thus method returns the utc equivalent of local time 12 yesterday. E.g. chile local 12 is in utc 16 and method
        return 16

        :return: the utc equivalent of local time 12 yesterday
        """
        yesterday = DateUtils.today_local_midday_in_utc() - datetime.timedelta(days=1)
        return yesterday

    @staticmethod
    def yesterday_local_midnight_in_utc() -> datetime.datetime:
        """
        Thus method returns the utc equivalent of local time 24 yesterday. E.g. chile local 24 monday is in utc 4
        tuesday and method return 4

        :return: the utc equivalent of local time 24 yesterday
        """
        midnight = DateUtils.today_local_midday_in_utc() - datetime.timedelta(hours=12)
        return midnight

    @staticmethod
    def yesterday_sunset_in_utc(lat, lon, elev) -> datetime.datetime:
        """Method calculate and return last night sunset"""
        sunset = calculate_sun_rise_set(date=DateUtils.yesterday_midday_utc(),
                                        horiz_height=0.0,
                                        sunrise=False,
                                        latitude=lat,
                                        longitude=lon,
                                        elevation=elev
                                        )
        return sunset

    @staticmethod
    def yesterday_sunrise_in_utc(lat, lon, elev) -> datetime.datetime:
        """Method calculate and return last night sunrise"""
        sunrise = calculate_sun_rise_set(date=DateUtils.yesterday_midday_utc(),
                                         horiz_height=0.0,
                                         sunrise=True,
                                         latitude=lat,
                                         longitude=lon,
                                         elevation=elev
                                         )
        return sunrise
