import dataclasses
import logging
from typing import Set

logger = logging.getLogger(__name__.rsplit('.')[-1])


@dataclasses.dataclass
class DataTypeFits:
    name: str
    count: int = 0
    filters: Set[str] = dataclasses.field(default_factory=lambda: set())
