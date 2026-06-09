import dataclasses
import datetime


@dataclasses.dataclass
class QualityLogMsg:
    LEVEL_NAMES = {
        10: 'DEBUG',
        20: 'INFO',
        25: 'NOTICE',
        30: 'WARNING',
        40: 'MAJOR'
    }

    date: datetime.datetime
    message: str
    level: int

    @property
    def level_name(self) -> str:
        try:
            return self.LEVEL_NAMES[self.level]
        except (ValueError, LookupError):
            return ''
