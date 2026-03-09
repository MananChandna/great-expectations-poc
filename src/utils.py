"""
utils.py — Shared utilities for the Great Expectations POC.

Provides logging configuration, path resolution, and helper functions
used across the project.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env if it exists
load_dotenv()


def get_project_root() -> Path:
    """Return the absolute path to the project root directory.

    Reads GX_PROJECT_ROOT from environment, defaulting to the parent
    of the src/ package directory.
    """
    env_root = os.environ.get("GX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    # Fallback: two levels up from this file (src/ → project root)
    return Path(__file__).resolve().parent.parent


def get_data_raw_dir() -> Path:
    """Return the path to the raw data directory."""
    root = get_project_root()
    subdir = os.environ.get("DATA_RAW_DIR", "data/raw")
    return root / subdir


def get_data_bad_dir() -> Path:
    """Return the path to the bad/dirty data directory."""
    root = get_project_root()
    subdir = os.environ.get("DATA_BAD_DIR", "data/bad_data")
    return root / subdir


def get_gx_context_dir() -> Path:
    """Return the path to the Great Expectations context directory."""
    root = get_project_root()
    subdir = os.environ.get("GX_CONTEXT_DIR", "gx")
    return root / subdir


def get_data_docs_dir() -> Path:
    """Return the path to the Data Docs output directory."""
    root = get_project_root()
    subdir = os.environ.get("DATA_DOCS_DIR", "gx/uncommitted/data_docs/local_site")
    return root / subdir


def setup_logging(name: str = "gx_poc") -> logging.Logger:
    """Configure and return a named logger.

    Log level is read from the LOG_LEVEL environment variable,
    defaulting to INFO. Logs are written to both stdout and a
    rotating file handler.

    Args:
        name: Logger name (typically the calling module's __name__).

    Returns:
        Configured Logger instance.
    """
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logger = logging.getLogger(name)
    if logger.handlers:
        # Avoid adding duplicate handlers on re-import
        return logger

    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    return logger


def ensure_directories(*dirs: Path) -> None:
    """Create directories if they do not already exist.

    Args:
        *dirs: One or more Path objects to create.
    """
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def print_separator(char: str = "═", width: int = 70) -> None:
    """Print a visual separator line to stdout.

    Args:
        char: Character to repeat.
        width: Total line width.
    """
    print(char * width)
