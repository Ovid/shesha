"""Tests for data models."""

from unittest.mock import MagicMock

from shesha.models import RepoProjectResult


class TestRepoProjectResult:
    """Tests for RepoProjectResult dataclass."""

    def test_created_status(self):
        """RepoProjectResult can be created with 'created' status."""
        mock_project = MagicMock()
        result = RepoProjectResult(
            project=mock_project,
            status="created",
            files_ingested=10,
            files_skipped=2,
            warnings=["some warning"],
        )

        assert result.project is mock_project
        assert result.status == "created"
        assert result.files_ingested == 10
        assert result.files_skipped == 2
        assert result.warnings == ["some warning"]

    def test_default_values(self):
        """RepoProjectResult has correct defaults for optional fields."""
        mock_project = MagicMock()
        result = RepoProjectResult(
            project=mock_project,
            status="created",
            files_ingested=5,
        )

        assert result.files_skipped == 0
        assert result.warnings == []

    def test_unchanged_status(self):
        """RepoProjectResult can be created with 'unchanged' status."""
        result = RepoProjectResult(
            project=MagicMock(),
            status="unchanged",
            files_ingested=0,
        )
        assert result.status == "unchanged"

    def test_updates_available_status(self):
        """RepoProjectResult can be created with 'updates_available' status."""
        result = RepoProjectResult(
            project=MagicMock(),
            status="updates_available",
            files_ingested=10,
        )
        assert result.status == "updates_available"
