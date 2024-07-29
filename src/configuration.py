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
                raise TypeError(f"a parameter of type {type(v)} was received and a parameter of type  "
                                f"{self.type} was expected")

    APP_NAME = 'halina'

    # keys
    NATS_HOST = "NATS_HOST"
    NATS_PORT = "NATS_PORT"
    TELESCOPE_NAMES = "TELESCOPE_NAMES"
    EMAILS_TO = "EMAILS"
    TIMEZONE = "TIMEZONE"
    SMTP_HOST = "SMTP_HOST"
    SMTP_PORT = "SMTP_PORT"
    FROM_EMAIL = "FROM_EMAIL"
    FROM_EMAIL_USER = "FROM_EMAIL_USER"
    EMAIL_APP_PASSWORD = "EMAIL_APP_PASSWORD"
    SEND_AT = "SEND_AT"

    __conf: Dict[str, __ConfigVal] = {
        NATS_HOST: __ConfigVal("localhost", str),
        NATS_PORT: __ConfigVal(4222, int),
        TELESCOPE_NAMES: __ConfigVal([], list),
        EMAILS_TO: __ConfigVal([], list),
        TIMEZONE: __ConfigVal(0, int),
        SMTP_HOST: __ConfigVal("smtp.gmail.com", str),
        SMTP_PORT: __ConfigVal(587, int),
        FROM_EMAIL: __ConfigVal("dchmal@akond.com", str),
        FROM_EMAIL_USER: __ConfigVal("Night Report Araucaria", str),
        EMAIL_APP_PASSWORD: __ConfigVal("", str),
        SEND_AT: __ConfigVal(14, int),  # at witch hour will be sent email
    }
    __setters = [NATS_HOST, NATS_PORT, TELESCOPE_NAMES, EMAILS_TO, TIMEZONE, SMTP_HOST, SMTP_PORT, FROM_EMAIL,
                 FROM_EMAIL_USER, EMAIL_APP_PASSWORD, SEND_AT]

    @classmethod
    def get(cls, name, default=None):
        cv = cls.__conf.get(name)
        if cv:
            return cv.val
        else:
            return default

    @classmethod
    def set(cls, name, value):
        if name in cls.__setters:
            cls.__conf.get(name).set_val(value)
        else:
            raise NameError("Name not accepted in set() method")
