import dataclasses
import datetime


@dataclasses.dataclass
class PowerPoint:
    date: datetime.datetime
    state_of_charge: float
    pv_power: float
    battery_charge: float
    battery_discharge: float
