import dataclasses
import datetime


@dataclasses.dataclass
class FwhmPoint:
    date: datetime.datetime
    fwhm: float
    scale: float