"""Tests for main Shesha class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from shesha import Shesha
from shesha.models import RepoProjectResult


class TestShesha:
    """Tests for Shesha class."""

    def test_create_project(self, tmp_path: Path):
        """Creating a project returns a Project instance."""
        with patch("shesha.shesha.ContainerPool"):
            shesha = Shesha(
                model="test-model",
                storage_path=tmp_path,
            )
            project = shesha.create_project("my-project")

            assert project.project_id == "my-project"

    def test_list_projects(self, tmp_path: Path):
        """List projects returns project IDs."""
        with patch("shesha.shesha.ContainerPool"):
            shesha = Shesha(model="test-model", storage_path=tmp_path)
            shesha.create_project("project-a")
            shesha.create_project("project-b")

            projects = shesha.list_projects()
            assert "project-a" in projects
            assert "project-b" in projects

    def test_get_project(self, tmp_path: Path):
        """Get project returns existing project."""
        with patch("shesha.shesha.ContainerPool"):
            shesha = Shesha(model="test-model", storage_path=tmp_path)
            shesha.create_project("existing")

            project = shesha.get_project("existing")
            assert project.project_id == "existing"

    def test_delete_project(self, tmp_path: Path):
        """Delete project removes it."""
        with patch("shesha.shesha.ContainerPool"):
            shesha = Shesha(model="test-model", storage_path=tmp_path)
            shesha.create_project("to-delete")
            shesha.delete_project("to-delete")

            assert "to-delete" not in shesha.list_projects()

    def test_register_parser(self, tmp_path: Path):
        """Register custom parser adds it to the registry."""
        with patch("shesha.shesha.ContainerPool"):
            shesha = Shesha(model="test-model", storage_path=tmp_path)

            # Create a mock custom parser
            mock_parser = MagicMock()
            mock_parser.can_parse.return_value = True

            shesha.register_parser(mock_parser)

            # The parser should now be in the registry
            assert mock_parser in shesha._parser_registry._parsers

    def test_stop_after_restart_stops_pool(self, tmp_path: Path):
        """Stop after start-stop-start cycle should stop the pool."""
        mock_pool = MagicMock()
        with patch("shesha.shesha.ContainerPool", return_value=mock_pool):
            shesha = Shesha(model="test-model", storage_path=tmp_path)

            # First cycle: start then stop
            shesha.start()
            shesha.stop()

            # Second cycle: start again
            shesha.start()

            # Reset call count to track second stop
            mock_pool.stop.reset_mock()

            # Second stop should call pool.stop()
            shesha.stop()

            mock_pool.stop.assert_called_once()


class TestCreateProjectFromRepo:
    """Tests for create_project_from_repo method."""

    def test_creates_new_project(self, tmp_path: Path):
        """create_project_from_repo creates project for new repo."""
        with patch("shesha.shesha.ContainerPool"):
            with patch("shesha.shesha.RepoIngester") as MockIngester:
                mock_ingester = MagicMock()
                MockIngester.return_value = mock_ingester

                mock_ingester.is_local_path.return_value = True
                mock_ingester.get_saved_sha.return_value = None
                mock_ingester.get_local_sha.return_value = "abc123"
                mock_ingester.list_files.return_value = ["src/main.py"]
                mock_ingester.repos_dir = tmp_path / "repos"

                shesha = Shesha(model="test-model", storage_path=tmp_path)

                with patch.object(shesha._parser_registry, "find_parser") as mock_find:
                    mock_parser = MagicMock()
                    mock_parser.parse.return_value = MagicMock(
                        name="main.py",
                        content="content",
                        format="py",
                        metadata={},
                        char_count=7,
                        parse_warnings=[],
                    )
                    mock_find.return_value = mock_parser

                    result = shesha.create_project_from_repo(
                        url="/path/to/local/repo",
                        name="my-project",
                    )

                assert isinstance(result, RepoProjectResult)
                assert result.status == "created"
                assert result.project.project_id == "my-project"

    def test_unchanged_when_sha_matches(self, tmp_path: Path):
        """create_project_from_repo returns unchanged when SHAs match."""
        with patch("shesha.shesha.ContainerPool"):
            with patch("shesha.shesha.RepoIngester") as MockIngester:
                mock_ingester = MagicMock()
                MockIngester.return_value = mock_ingester

                mock_ingester.is_local_path.return_value = False
                mock_ingester.get_saved_sha.return_value = "abc123"
                mock_ingester.get_remote_sha.return_value = "abc123"

                shesha = Shesha(model="test-model", storage_path=tmp_path)
                shesha._storage.create_project("my-project")

                result = shesha.create_project_from_repo(
                    url="https://github.com/org/repo",
                    name="my-project",
                )

                assert result.status == "unchanged"

    def test_updates_available_when_sha_differs(self, tmp_path: Path):
        """create_project_from_repo returns updates_available when SHAs differ."""
        with patch("shesha.shesha.ContainerPool"):
            with patch("shesha.shesha.RepoIngester") as MockIngester:
                mock_ingester = MagicMock()
                MockIngester.return_value = mock_ingester

                mock_ingester.is_local_path.return_value = False
                mock_ingester.get_saved_sha.return_value = "abc123"
                mock_ingester.get_remote_sha.return_value = "def456"

                shesha = Shesha(model="test-model", storage_path=tmp_path)
                shesha._storage.create_project("my-project")

                result = shesha.create_project_from_repo(
                    url="https://github.com/org/repo",
                    name="my-project",
                )

                assert result.status == "updates_available"
