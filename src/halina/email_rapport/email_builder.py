import logging

logger = logging.getLogger(__name__.rsplit('.')[-1])


class EmailBuilder:
    # todo zrobić tak jak w modelach w java
    def __init__(self):
        self._date = None

    def set_date(self, date):
        self._date = date

    def date(self, date):
        self._date = date
        return self

    async def build(self) -> str:
        """this method return complete email as string"""
        return ""