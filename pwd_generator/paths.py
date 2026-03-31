"""Default paths for logs and application data (no extra dependencies)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def default_log_file_path() -> Path:
    """Return path for the default application log file; parent dirs are created."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Logs" / "HorizonCipher"
    else:
        xdg = os.environ.get("XDG_STATE_HOME")
        if xdg:
            base = Path(xdg) / "horizon-cipher"
        else:
            base = Path.home() / ".local" / "state" / "horizon-cipher"
    base.mkdir(parents=True, exist_ok=True)
    return base / "password_generator.log"
