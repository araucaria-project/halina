import dataclasses
import datetime


@dataclasses.dataclass
class QualityQmapPoint:
    date: datetime.datetime
    ratio_no_bkg_1: float
    # ratio_no_bkg_2: float
    # ratio_no_bkg_3: float
    # ratio_no_bkg_4: float
    # ratio_0: float
    # ratio_1: float
    # ratio_2: float
    # ratio_3: float
    # ratio_4: float
    # sum_0: float
    # sum_1: float
    # sum_2: float
    # sum_3: float
    # sum_4: float