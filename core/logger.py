import logging
from pathlib import Path


def setup_logger():

    Path("logs").mkdir(exist_ok=True)

    logger = logging.getLogger("AivisVoiceBridge")

    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(message)s",
        "%H:%M:%S"
    )

    file_handler = logging.FileHandler(
        "logs/latest.log",
        encoding="utf-8"
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger