import dataclasses
from halina.email_rapport.data_collector_classes.range_chart_point import RangeChartPoint


@dataclasses.dataclass
class ObjectChartPoint(RangeChartPoint):
    name: str
    filter: str
    type: str
    alt: float

    @property
    def is_max_alt(self) -> bool:
        pass

    @property
    def is_min_alt(self) -> bool:
        pass

    @property
    def is_obs_min_alt(self) -> bool:
        pass
