"""
Data Object module.

This module defines the DataObject class which represents a data structure for holding telescope data.

Classes:
    - DataObject: Represents a data structure for holding telescope data.
"""

import dataclasses
import logging
from typing import List, Set

logger = logging.getLogger(__name__.rsplit('.')[-1])


@dataclasses.dataclass
class DataObject:
    name: str
    count: int = 0
    filters: Set[str] = dataclasses.field(default_factory=lambda: set())
