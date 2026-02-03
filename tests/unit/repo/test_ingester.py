"""Tests for RepoIngester."""

import os
from pathlib import Path
from unittest.mock import patch

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

    def test_detect_host_github(self, ingester: RepoIngester):
        """detect_host identifies GitHub URLs."""
        assert ingester.detect_host("https://github.com/org/repo") == "github.com"
        assert ingester.detect_host("git@github.com:org/repo.git") == "github.com"

    def test_detect_host_gitlab(self, ingester: RepoIngester):
        """detect_host identifies GitLab URLs."""
        assert ingester.detect_host("https://gitlab.com/org/repo") == "gitlab.com"

    def test_detect_host_bitbucket(self, ingester: RepoIngester):
        """detect_host identifies Bitbucket URLs."""
        assert ingester.detect_host("https://bitbucket.org/org/repo") == "bitbucket.org"

    def test_detect_host_local(self, ingester: RepoIngester):
        """detect_host returns None for local paths."""
        assert ingester.detect_host("/home/user/repo") is None


class TestTokenResolution:
    """Tests for token resolution logic."""

    def test_explicit_token_takes_precedence(self, ingester: RepoIngester):
        """Explicit token parameter wins over env vars."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}):
            token = ingester.resolve_token(
                url="https://github.com/org/repo",
                explicit_token="explicit_token",
            )
            assert token == "explicit_token"

    def test_github_env_token(self, ingester: RepoIngester):
        """GITHUB_TOKEN env var used for github.com."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "gh_token"}, clear=True):
            token = ingester.resolve_token(
                url="https://github.com/org/repo",
                explicit_token=None,
            )
            assert token == "gh_token"

    def test_gitlab_env_token(self, ingester: RepoIngester):
        """GITLAB_TOKEN env var used for gitlab.com."""
        with patch.dict(os.environ, {"GITLAB_TOKEN": "gl_token"}, clear=True):
            token = ingester.resolve_token(
                url="https://gitlab.com/org/repo",
                explicit_token=None,
            )
            assert token == "gl_token"

    def test_no_token_returns_none(self, ingester: RepoIngester):
        """Returns None when no token available."""
        with patch.dict(os.environ, {}, clear=True):
            token = ingester.resolve_token(
                url="https://github.com/org/repo",
                explicit_token=None,
            )
            assert token is None
