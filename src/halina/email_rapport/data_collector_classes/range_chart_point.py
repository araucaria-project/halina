import dataclasses
import datetime


@dataclasses.dataclass
class RangeChartPoint:
    start: datetime.datetime
    end: datetime.datetime
