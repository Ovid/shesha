"""Filesystem-based storage backend."""

import json
import shutil
from pathlib import Path

from shesha.exceptions import (
    DocumentNotFoundError,
    ProjectExistsError,
    ProjectNotFoundError,
)
from shesha.models import ParsedDocument


class FilesystemStorage:
    """Store projects and documents on the local filesystem."""

    def __init__(self, root_path: Path | str, keep_raw_files: bool = False) -> None:
        """Initialize storage with a root directory."""
        self.root = Path(root_path)
        self.projects_dir = self.root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.keep_raw_files = keep_raw_files

    def _project_path(self, project_id: str) -> Path:
        """Get the path for a project directory."""
        return self.projects_dir / project_id

    def create_project(self, project_id: str) -> None:
        """Create a new project."""
        project_path = self._project_path(project_id)
        if project_path.exists():
            raise ProjectExistsError(project_id)
        project_path.mkdir()
        (project_path / "docs").mkdir()
        if self.keep_raw_files:
            (project_path / "raw").mkdir()
        # Write project metadata
        meta = {"id": project_id, "created": True}
        (project_path / "_meta.json").write_text(json.dumps(meta))

    def delete_project(self, project_id: str) -> None:
        """Delete a project and all its documents."""
        project_path = self._project_path(project_id)
        if project_path.exists():
            shutil.rmtree(project_path)

    def list_projects(self) -> list[str]:
        """List all project IDs."""
        if not self.projects_dir.exists():
            return []
        return [
            p.name
            for p in self.projects_dir.iterdir()
            if p.is_dir() and (p / "_meta.json").exists()
        ]

    def project_exists(self, project_id: str) -> bool:
        """Check if a project exists."""
        project_path = self._project_path(project_id)
        return project_path.exists() and (project_path / "_meta.json").exists()

    def store_document(
        self, project_id: str, doc: ParsedDocument, raw_path: Path | None = None
    ) -> None:
        """Store a parsed document in a project."""
        if not self.project_exists(project_id):
            raise ProjectNotFoundError(project_id)
        docs_dir = self._project_path(project_id) / "docs"
        doc_path = docs_dir / f"{doc.name}.json"
        doc_data = {
            "name": doc.name,
            "content": doc.content,
            "format": doc.format,
            "metadata": doc.metadata,
            "char_count": doc.char_count,
            "parse_warnings": doc.parse_warnings,
        }
        doc_path.write_text(json.dumps(doc_data, indent=2))

        # Store raw file if enabled and path provided
        if self.keep_raw_files and raw_path is not None:
            raw_dir = self._project_path(project_id) / "raw"
            raw_dir.mkdir(exist_ok=True)
            shutil.copy2(raw_path, raw_dir / doc.name)

    def get_document(self, project_id: str, doc_name: str) -> ParsedDocument:
        """Retrieve a document by name."""
        if not self.project_exists(project_id):
            raise ProjectNotFoundError(project_id)
        doc_path = self._project_path(project_id) / "docs" / f"{doc_name}.json"
        if not doc_path.exists():
            raise DocumentNotFoundError(project_id, doc_name)
        doc_data = json.loads(doc_path.read_text())
        return ParsedDocument(**doc_data)

    def list_documents(self, project_id: str) -> list[str]:
        """List all document names in a project."""
        if not self.project_exists(project_id):
            raise ProjectNotFoundError(project_id)
        docs_dir = self._project_path(project_id) / "docs"
        return [p.stem for p in docs_dir.glob("*.json")]

    def delete_document(self, project_id: str, doc_name: str) -> None:
        """Delete a document from a project."""
        if not self.project_exists(project_id):
            raise ProjectNotFoundError(project_id)
        doc_path = self._project_path(project_id) / "docs" / f"{doc_name}.json"
        if doc_path.exists():
            doc_path.unlink()

    def load_all_documents(self, project_id: str) -> list[ParsedDocument]:
        """Load all documents in a project for querying."""
        doc_names = self.list_documents(project_id)
        return [self.get_document(project_id, name) for name in doc_names]
