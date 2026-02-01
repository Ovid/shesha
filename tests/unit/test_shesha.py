"""Tests for main Shesha class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from shesha import Shesha


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
