"""Tests for RepoIngester."""

from pathlib import Path

import pytest

from shesha.repo.ingester import RepoIngester


@pytest.fixture
def ingester(tmp_path: Path) -> RepoIngester:
    return RepoIngester(storage_path=tmp_path)


class TestRepoIngester:
    """Tests for RepoIngester class."""

    def test_init_creates_repos_dir(self, ingester: RepoIngester, tmp_path: Path):
        """RepoIngester creates repos directory on init."""
        assert (tmp_path / "repos").is_dir()

    def test_is_local_path_absolute(self, ingester: RepoIngester):
        """is_local_path returns True for absolute paths."""
        assert ingester.is_local_path("/home/user/repo")

    def test_is_local_path_home(self, ingester: RepoIngester):
        """is_local_path returns True for home-relative paths."""
        assert ingester.is_local_path("~/projects/repo")

    def test_is_local_path_url(self, ingester: RepoIngester):
        """is_local_path returns False for URLs."""
        assert not ingester.is_local_path("https://github.com/org/repo")
        assert not ingester.is_local_path("git@github.com:org/repo.git")
