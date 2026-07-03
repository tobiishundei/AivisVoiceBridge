"""
AivisVoiceBridge 共通 logger を設定する。

コンソールと logs/latest.log の両方へ同じ形式でログを出力する。
setup_logger() は複数回呼ばれても handler が重複しないようにする。
"""

import logging
from pathlib import Path


LOGGER_NAME = "AivisVoiceBridge"
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "latest.log"


def setup_logger():
    """
    アプリ全体で使う logger を生成して返す。
    """

    LOG_DIR.mkdir(
        exist_ok=True
    )

    logger = logging.getLogger(
        LOGGER_NAME
    )

    logger.setLevel(
        logging.INFO
    )

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(message)s",
        "%H:%M:%S",
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )

    file_handler.setFormatter(
        formatter
    )

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )

    logger.addHandler(
        console_handler
    )

    return logger