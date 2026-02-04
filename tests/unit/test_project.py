"""Tests for Project class."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shesha.models import ParsedDocument
from shesha.project import Project
from shesha.rlm.trace import StepType


@pytest.fixture
def mock_storage() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_registry() -> MagicMock:
    registry = MagicMock()
    parser = MagicMock()
    parser.parse.return_value = ParsedDocument(
        name="test.txt",
        content="content",
        format="txt",
        metadata={},
        char_count=7,
        parse_warnings=[],
    )
    registry.find_parser.return_value = parser
    return registry


class TestProject:
    """Tests for Project."""

    def test_upload_file(self, mock_storage: MagicMock, mock_registry: MagicMock, tmp_path: Path):
        """Upload parses and stores a file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        project = Project(
            project_id="test-project",
            storage=mock_storage,
            parser_registry=mock_registry,
        )
        project.upload(test_file)

        mock_storage.store_document.assert_called_once()

    def test_list_documents(self, mock_storage: MagicMock, mock_registry: MagicMock):
        """List documents returns storage list."""
        mock_storage.list_documents.return_value = ["a.txt", "b.txt"]

        project = Project(
            project_id="test-project",
            storage=mock_storage,
            parser_registry=mock_registry,
        )
        docs = project.list_documents()

        assert docs == ["a.txt", "b.txt"]

    def test_delete_document(self, mock_storage: MagicMock, mock_registry: MagicMock):
        """Delete document calls storage."""
        project = Project(
            project_id="test-project",
            storage=mock_storage,
            parser_registry=mock_registry,
        )
        project.delete_document("old.txt")

        mock_storage.delete_document.assert_called_with("test-project", "old.txt")

    def test_query_passes_on_progress_to_engine(
        self, mock_storage: MagicMock, mock_registry: MagicMock
    ):
        """Query passes on_progress callback and documents to RLM engine."""
        # Mock the engine
        mock_engine = MagicMock()
        mock_engine.query.return_value = MagicMock(answer="test answer")

        # Mock storage.load_all_documents to return real document objects
        mock_storage.load_all_documents.return_value = [
            ParsedDocument(
                name="doc.txt",
                content="doc content",
                format="txt",
                metadata={},
                char_count=11,
                parse_warnings=[],
            )
        ]

        project = Project(
            project_id="test-project",
            storage=mock_storage,
            parser_registry=mock_registry,
            rlm_engine=mock_engine,
        )

        # Create a callback
        def on_progress(step_type: StepType, iteration: int, content: str) -> None:
            pass

        project.query("test question", on_progress=on_progress)

        # Verify load_all_documents was called with project_id
        mock_storage.load_all_documents.assert_called_once_with("test-project")

        # Verify engine.query received correct arguments
        mock_engine.query.assert_called_once()
        call_kwargs = mock_engine.query.call_args.kwargs
        assert call_kwargs.get("on_progress") is on_progress
        assert call_kwargs.get("documents") == ["doc content"]
        assert call_kwargs.get("doc_names") == ["doc.txt"]
        assert call_kwargs.get("question") == "test question"

    def test_query_passes_none_storage_for_non_filesystem_backend(
        self, mock_storage: MagicMock, mock_registry: MagicMock
    ):
        """Query passes None for storage when backend is not FilesystemStorage."""
        mock_engine = MagicMock()
        mock_engine.query.return_value = MagicMock(answer="test answer")

        mock_storage.load_all_documents.return_value = [
            ParsedDocument(
                name="doc.txt",
                content="doc content",
                format="txt",
                metadata={},
                char_count=11,
                parse_warnings=[],
            )
        ]

        project = Project(
            project_id="test-project",
            storage=mock_storage,
            parser_registry=mock_registry,
            rlm_engine=mock_engine,
        )

        project.query("test question")

        # Non-FilesystemStorage results in None being passed (tracing disabled)
        call_kwargs = mock_engine.query.call_args.kwargs
        assert call_kwargs.get("storage") is None
        assert call_kwargs.get("project_id") == "test-project"

    def test_query_passes_filesystem_storage_for_tracing(self, mock_registry: MagicMock):
        """Query passes FilesystemStorage to engine for trace writing."""
        from unittest.mock import create_autospec

        from shesha.storage.filesystem import FilesystemStorage

        mock_engine = MagicMock()
        mock_engine.query.return_value = MagicMock(answer="test answer")

        # Use autospec to create a mock that passes isinstance check
        fs_storage = create_autospec(FilesystemStorage, instance=True)
        fs_storage.load_all_documents.return_value = [
            ParsedDocument(
                name="doc.txt",
                content="doc content",
                format="txt",
                metadata={},
                char_count=11,
                parse_warnings=[],
            )
        ]

        project = Project(
            project_id="test-project",
            storage=fs_storage,
            parser_registry=mock_registry,
            rlm_engine=mock_engine,
        )

        project.query("test question")

        # FilesystemStorage should be passed for trace writing
        call_kwargs = mock_engine.query.call_args.kwargs
        assert call_kwargs.get("storage") is fs_storage
        assert call_kwargs.get("project_id") == "test-project"
