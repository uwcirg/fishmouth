import json
import logging
import time


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include exception details if they exist
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        return time.strftime("%Y-%m-%dT%H:%M:%S", ct) + f'.{int(record.msecs):03d}Z'
