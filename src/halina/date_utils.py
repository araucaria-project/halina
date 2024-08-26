import datetime
import logging

from configuration import GlobalConfig

logger = logging.getLogger(__name__.rsplit('.')[-1])


class DateUtils:

    @staticmethod
    def today_midday() -> datetime:
        t = datetime.datetime.today()
        t = t.replace(hour=12, minute=0, second=0, microsecond=0)  # set yesterday at middle of the day
        t = t + datetime.timedelta(hours=GlobalConfig.get(GlobalConfig.TIMEZONE, 0))  # set local time
        return t

    @staticmethod
    def yesterday_midday() -> datetime:
        yesterday = DateUtils.today_midday() - datetime.timedelta(days=1)
        return yesterday
