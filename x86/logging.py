"""
logging.py: Structured logging under ~/Library/Logs/26x86/
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .manifest import PATCHER_VERSION
from .paths import Paths


def resolve_logs_dir() -> Path:
    base_path = Paths.user_logs_dir().expanduser()
    if sys.platform == "darwin" and str(base_path).startswith("/var/root/"):
        base_path = Path("/var/tmp/26x86")
    try:
        base_path.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as error:
        print(f"Failed to create 26x86 log folder: {error}", file=sys.stderr)
        base_path = Path(tempfile.gettempdir()) / "26x86"
        base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def build_log_filepath(logs_dir: Optional[Path] = None) -> Path:
    logs_dir = logs_dir or resolve_logs_dir()
    log_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    return logs_dir / f"26x86_{PATCHER_VERSION}_{log_time}.log"


def setup_logging(
    *,
    verbose: bool = False,
    log_filepath: Optional[Path] = None,
) -> Path:
    """
    Configure root logger for CLI/GUI sessions.
    Returns the log file path used.
    """
    logs_dir = resolve_logs_dir()
    log_filepath = log_filepath or build_log_filepath(logs_dir)

    level = logging.DEBUG if verbose or os.environ.get("X86_VERBOSE") == "1" else logging.INFO

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        log_filepath,
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    stream_handler.setLevel(level)
    root.addHandler(stream_handler)

    return log_filepath
