"""
logger.py - Colored console + file logging
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import colorlog

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # ── Console handler (coloured) ──────────────────────────────────────────────
    console = colorlog.StreamHandler()
    console.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)-8s] %(name)s%(reset)s  %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )
    logger.addHandler(console)

    # ── File handler ────────────────────────────────────────────────────────────
    today = datetime.utcnow().strftime("%Y-%m-%d")
    fh = logging.FileHandler(LOG_DIR / f"bot_{today}.log")
    fh.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)s  %(message)s")
    )
    logger.addHandler(fh)

    return logger
