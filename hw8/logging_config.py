"""Единая настройка логирования для API и воркера."""
import logging

from config import LOG_LEVEL


def setup_app_logging() -> None:
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format=fmt, datefmt=datefmt)
    else:
        root.setLevel(level)
        for h in root.handlers:
            h.setLevel(level)

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "httpx", "asyncio"):
        logging.getLogger(name).setLevel(level)
