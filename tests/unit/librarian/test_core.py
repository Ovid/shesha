"""Tests for LibrarianCore."""

from pathlib import Path

import pytest

from shesha.librarian.core import LibrarianCore, ValidationError


def test_upload_requires_existing_path(tmp_path: Path) -> None:
    """Upload fails fast with a clear error when the path does not exist."""
    storage_path = tmp_path / "storage"
    core = LibrarianCore(storage_path=storage_path)
    core.create_project("p1")

    with pytest.raises(ValidationError) as exc_info:
        core.upload("p1", tmp_path / "missing.txt")

    assert "not found" in str(exc_info.value).lower()

