import logging

from pythonjsonlogger import jsonlogger


def setup_logging():
    logger = logging.getLogger()

    # Clear existing handlers (this is key)
    logger.handlers.clear()

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
