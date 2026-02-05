"""Tests for Librarian path resolution."""

from pathlib import Path

from shesha.librarian.paths import resolve_paths


def test_resolve_paths_prefers_librarian_home(monkeypatch, tmp_path: Path) -> None:
    """LIBRARIAN_HOME overrides platform defaults."""
    home = tmp_path / "librarian-home"
    monkeypatch.setenv("LIBRARIAN_HOME", str(home))
    monkeypatch.delenv("LIBRARIAN_STORAGE_PATH", raising=False)
    monkeypatch.delenv("LIBRARIAN_LOG_DIR", raising=False)

    paths = resolve_paths()

    assert paths.home == home
    assert paths.storage == home / "storage"
    assert paths.logs == home / "logs"


def test_resolve_paths_prefers_explicit_storage_path(monkeypatch, tmp_path: Path) -> None:
    """LIBRARIAN_STORAGE_PATH has highest precedence for storage."""
    monkeypatch.setenv("LIBRARIAN_HOME", str(tmp_path / "ignored-home"))
    storage = tmp_path / "custom-storage"
    monkeypatch.setenv("LIBRARIAN_STORAGE_PATH", str(storage))
    monkeypatch.delenv("LIBRARIAN_LOG_DIR", raising=False)

    paths = resolve_paths()

    assert paths.storage == storage
    # Logs should still be under LIBRARIAN_HOME when LOG_DIR is not provided.
    assert paths.logs == (tmp_path / "ignored-home" / "logs")


def test_resolve_paths_allows_custom_log_dir(monkeypatch, tmp_path: Path) -> None:
    """LIBRARIAN_LOG_DIR overrides default log directory."""
    home = tmp_path / "librarian-home"
    log_dir = tmp_path / "custom-logs"
    monkeypatch.setenv("LIBRARIAN_HOME", str(home))
    monkeypatch.setenv("LIBRARIAN_LOG_DIR", str(log_dir))
    monkeypatch.delenv("LIBRARIAN_STORAGE_PATH", raising=False)

    paths = resolve_paths()

    assert paths.storage == home / "storage"
    assert paths.logs == log_dir

