import dataclasses
from typing import Dict
from dynaconf import Dynaconf

from definitions import CONFIG_DIR


class GlobalConfig:
    @dataclasses.dataclass
    class __ConfigVal:
        type: type
        val: object = None

        def __init__(self, type_):
            self.val = None
            self.type: type = type_

        def set_val(self, v):
            if isinstance(v, self.type):
                self.val = v
            else:
                raise TypeError(f"a parameter of type {type(v)} was received and a parameter of type  "
                                f"{self.type} was expected")

    # Dynaconf source
    __settings = Dynaconf(
        settings_files=[f'{CONFIG_DIR}/default_settings.toml',
                        f'{CONFIG_DIR}/settings.toml',
                        '/usr/local/etc/halina/settings.toml'],
    )

    APP_NAME = 'halina'

    # keys
    NATS_HOST = "NATS_HOST"
    NATS_PORT = "NATS_PORT"
    SMTP_HOST = "SMTP_HOST"
    SMTP_PORT = "SMTP_PORT"
    SMTP_USERNAME = "SMTP_USERNAME"
    TELESCOPES = "TELESCOPES"
    EMAILS_TO = "EMAILS_TO"
    OBSERVATORY_TIMEZONE = "OBSERVATORY_TIMEZONE"
    FROM_EMAIL = "FROM_EMAIL"
    FROM_NAME = "FROM_NAME"
    SMTP_PASSWORD = "SMTP_PASSWORD"
    SEND_AT = "SEND_AT"
    SEND_AT_MIN = "SEND_AT_MIN"
    RAPPORT_FILE_TARGET_PATH = "RAPPORT_FILE_TARGET_PATH"
    CHARTS_UTC_OFFSET_HOURS = "CHARTS_UTC_OFFSET_HOURS"

    # dict of empty values. If someone will be overridden by not None value, this value will be return instead
    # value from config
    __conf: Dict[str, __ConfigVal] = {
        NATS_HOST: __ConfigVal(str),
        NATS_PORT: __ConfigVal(int),
        SMTP_USERNAME: __ConfigVal(str),
        TELESCOPES: __ConfigVal(list),
        EMAILS_TO: __ConfigVal(list),
        OBSERVATORY_TIMEZONE: __ConfigVal(int),
        SMTP_HOST: __ConfigVal(str),
        SMTP_PORT: __ConfigVal(int),
        FROM_EMAIL: __ConfigVal(str),
        FROM_NAME: __ConfigVal(str),
        SMTP_PASSWORD: __ConfigVal(str),
        CHARTS_UTC_OFFSET_HOURS: __ConfigVal(float),
        SEND_AT: __ConfigVal(int),  # at witch hour will be sent email
        RAPPORT_FILE_TARGET_PATH: __ConfigVal(str),  # at witch hour will be sent email
    }
    # __setters = [NATS_HOST, NATS_PORT, SMTP_USERNAME, TELESCOPES, EMAILS_TO, OBSERVATORY_TIMEZONE, SMTP_HOST,
    # SMTP_PORT, FROM_EMAIL, FROM_NAME, SMTP_PASSWORD, SEND_AT]

    @classmethod
    def get(cls, name, default=None):
        cv = cls.__conf.get(name)
        if cv and cv.val is not None:
            return cv.val
        else:
            return cls.__settings.get(name, default)

    @classmethod
    def set(cls, name, value):
        if name in cls.__conf:
            cls.__conf.get(name).set_val(value)
        else:
            raise NameError("Name not accepted in set() method")
