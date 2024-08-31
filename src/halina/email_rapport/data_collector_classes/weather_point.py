import dataclasses
import datetime


@dataclasses.dataclass
class WeatherPoint:
    date: datetime.datetime
    temperature: float
    humidity: int
    wind: float
    wind_dir_deg: int
    pressure: float
