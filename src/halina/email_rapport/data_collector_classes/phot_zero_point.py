import dataclasses
import datetime


@dataclasses.dataclass
class PhotZeroPoint:
    date: datetime.datetime
    filter_: str
    zero_point: float
