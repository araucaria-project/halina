from threading import Lock

from halina.service_communication import ServiceCommunication


class ServiceSharedDataSingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class ServiceSharedData(metaclass=ServiceSharedDataSingletonMeta):
    _data_lock: Lock = Lock()

    def __init__(self):
        self._events: ServiceCommunication = ServiceCommunication()
        self._data = {}

    def get(self, name, default=None):
        with self._data_lock:
            return self._data.get(name, default)

    def set(self, name, value):
        with self._data_lock:
            self._data[name] = value

    def has(self, name) -> bool:
        return name in self._data

    def get_events(self) -> ServiceCommunication:
        return self._events
