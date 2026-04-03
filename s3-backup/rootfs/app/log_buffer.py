import logging
import time
from collections import deque


class LogBuffer(logging.Handler):
    def __init__(self, maxlen: int = 500):
        super().__init__()
        self._buffer: deque = deque(maxlen=maxlen)
        self.setFormatter(logging.Formatter("%(name)s - %(message)s"))

    def emit(self, record: logging.LogRecord):
        self._buffer.append(
            {
                "time": record.created,
                "level": record.levelname,
                "message": self.format(record),
            }
        )

    def get_logs(self) -> list:
        return list(reversed(self._buffer))
