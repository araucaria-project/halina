import dataclasses
from typing import List, Optional

from halina.email_rapport.data_collector_classes.object_chart_point import ObjectChartPoint
from halina.email_rapport.data_collector_classes.range_chart_point import RangeChartPoint


@dataclasses.dataclass
class ObservationChartData:
    tel_name: str
    tel_lat: Optional[float] = None
    tel_lon: Optional[float] = None
    tel_elev: Optional[float] = None
    objects: List[ObjectChartPoint] = dataclasses.field(default_factory=lambda: [])  # set default empty list
    dome: List[RangeChartPoint] = dataclasses.field(default_factory=lambda: [])  # set default empty list
    fans: List[RangeChartPoint] = dataclasses.field(default_factory=lambda: [])  # set default empty list
    filter_color_map: dict = dataclasses.field(default_factory=lambda: {})  # set default empty dict
    alt_map: dict = dataclasses.field(default_factory=lambda: {})  # set default empty dict
