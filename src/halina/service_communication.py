import asyncio


class ServiceCommunication:

    def __init__(self):
        self._data = {}

    def get(self, name) -> asyncio.Event:
        """
        Method return event.

        :param name: evnet name
        :return: asyncio.Event object
        """
        return self._data.get(name)

    def set(self, name, val: asyncio.Event):
        """
        Method add nev event

        :param name: evnet name
        :param val: asyncio.Event object
        """
        self._data[name] = val

    def notify(self, name) -> bool:
        """
        Method set and clear asyncio event.

        :param name: evnet name
        :return: true if event was call successfully and false if not
        """
        e = self.get(name)
        if e:
            e.set()
            e.clear()
            return True
        return False

    async def wait(self, name):
        """
        Method wait for event set.

        :param name: evnet name
        """
        e = self.get(name)
        if e:
            await e.wait()

    def is_exist(self, name):
        """
        Method check event exist.

        :param name: evnet name
        :return: true if event exist
        """
        return self.get(name) is not None
