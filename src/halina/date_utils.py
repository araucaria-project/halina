"""
Date Utilities module.

This module provides utility functions for handling date and time operations.

Classes:
    - DateUtils: Provides static methods for date manipulations.
"""

import datetime
import logging

from configuration import GlobalConfig

logger = logging.getLogger(__name__.rsplit('.')[-1])


class DateUtils:
    """
    Provides static methods for date manipulations.
    """

    @staticmethod
    def today_midday() -> datetime.datetime:
        """
        Gets the current day's midday time.

        Returns:
            datetime.datetime: Today's date with time set to midday.
        """
        t = datetime.datetime.today()
        t = t.replace(hour=12, minute=0, second=0, microsecond=0)  # set today at midday
        t = t + datetime.timedelta(hours=GlobalConfig.get(GlobalConfig.TIMEZONE))  # set local time
        return t

    @staticmethod
    def yesterday_midday() -> datetime.datetime:
        """
        Gets the previous day's midday time.

        Returns:
            datetime.datetime: Yesterday's date with time set to midday.
        """
        yesterday = DateUtils.today_midday() - datetime.timedelta(days=1)
        return yesterday
