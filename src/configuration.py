import dataclasses
from asyncio import Lock
from typing import Optional, Dict


# class SingletonMeta(type):
#     _instances = {}
#     _lock: Lock = Lock()
#
#     def __call__(cls, *args, **kwargs):
#         """
#         Possible changes to the value of the `__init__` argument do not affect
#         the returned instance.
#         """
#         with cls._lock:
#             if cls not in cls._instances:
#                 instance = super().__call__(*args, **kwargs)
#                 cls._instances[cls] = instance
#         return cls._instances[cls]


class GlobalConfig:
    @dataclasses.dataclass
    class __ConfigVal:
        val: object
        type: type
        is_optional: bool = False

        def __init__(self, val, type_, is_optional=False):
            self.val = val
            self.type: type = type_
            self.is_optional = is_optional

        def set_val(self, v):
            if isinstance(v, self.type) or (self.is_optional and v is None):
                self.val = v
            else:
                raise TypeError

    APP_NAME = 'halina'

    # keys
    NATS_HOST = "NATS_HOST"
    NATS_PORT = "NATS_PORT"
    TELESCOPES_NAME = "TELESCOPES_NAME"
    EMAILS_TO = "EMAILS"
    TIMEZONE = "TIMEZONE"

    __conf: Dict[str, __ConfigVal] = {
        NATS_HOST: __ConfigVal("localhost", str),
        NATS_PORT: __ConfigVal(4222, int),
        TELESCOPES_NAME: __ConfigVal([], list),
        EMAILS_TO: __ConfigVal([], list),
        TIMEZONE: __ConfigVal(0, int)
    }
    __setters = [NATS_HOST, NATS_PORT, TELESCOPES_NAME, EMAILS_TO, TIMEZONE]

    @staticmethod
    def get(name, default=None):
        cv = GlobalConfig.__conf.get(name)
        if cv:
            return cv.val
        else:
            return default

    @staticmethod
    def set(name, value):
        if name in GlobalConfig.__setters:
            GlobalConfig.__conf.get(name).set_val(value)
        else:
            raise NameError("Name not accepted in set() method")


