"""Tests for Librarian CLI helpers."""

from pathlib import Path

from shesha.librarian import cli


def test_sandbox_source_dir_points_to_dockerfile() -> None:
    """The source checkout includes the sandbox Dockerfile used for self-test/build."""
    sandbox_dir = cli._sandbox_source_dir()
    assert sandbox_dir is not None
    dockerfile = sandbox_dir / "Dockerfile"
    assert dockerfile.exists()
    assert dockerfile.is_file()

