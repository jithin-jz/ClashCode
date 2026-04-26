import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """

    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }

        # Handle exceptions
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Handle extra fields if passed
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)

        return json.dumps(log_record)


def setup_logging():
    """
    Configures the root logger to use JSON formatting on stdout.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)
