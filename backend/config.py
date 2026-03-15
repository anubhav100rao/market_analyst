"""
Centralized logging configuration.

All modules should import the logger from here:
    from backend.config import logger

Logs are written to both console and dump.log.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOG_FILE = os.getenv("LOG_FILE", "dump.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ── Formatter ──────────────────────────────────────────────────────
_fmt = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── File handler → dump.log ───────────────────────────────────────
_file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
_file_handler.setFormatter(_fmt)
_file_handler.setLevel(LOG_LEVEL)

# ── Console handler ──────────────────────────────────────────────
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_fmt)
_console_handler.setLevel(LOG_LEVEL)

# ── Root project logger ──────────────────────────────────────────
logger = logging.getLogger("market_analyst")
logger.setLevel(LOG_LEVEL)
logger.addHandler(_file_handler)
logger.addHandler(_console_handler)
logger.propagate = False

# ── Env helpers ──────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

logger.info("Logger initialised – level=%s, file=%s", LOG_LEVEL, LOG_FILE)
