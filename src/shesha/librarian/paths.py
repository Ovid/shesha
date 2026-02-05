"""Path resolution for Librarian state (storage + logs)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LibrarianPaths:
    """Resolved state paths for Librarian."""

    home: Path
    storage: Path
    logs: Path

    def ensure_dirs(self) -> None:
        """Create storage/log directories if missing."""
        self.home.mkdir(parents=True, exist_ok=True)
        self.storage.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)


def _default_home_dir() -> Path:
    home = Path.home()

    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Librarian"

    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Librarian"
        return home / "AppData" / "Roaming" / "Librarian"

    xdg_data = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data) if xdg_data else (home / ".local" / "share")
    return base / "librarian"


def resolve_paths() -> LibrarianPaths:
    """Resolve Librarian state directories using environment overrides."""
    home_env = os.environ.get("LIBRARIAN_HOME")
    home_dir = Path(home_env).expanduser() if home_env else _default_home_dir()

    storage_env = os.environ.get("LIBRARIAN_STORAGE_PATH")
    storage_dir = Path(storage_env).expanduser() if storage_env else (home_dir / "storage")

    logs_env = os.environ.get("LIBRARIAN_LOG_DIR")
    logs_dir = Path(logs_env).expanduser() if logs_env else (home_dir / "logs")

    return LibrarianPaths(home=home_dir, storage=storage_dir, logs=logs_dir)

