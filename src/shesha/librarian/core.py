"""Core operations shared by the Librarian CLI and MCP server."""

from __future__ import annotations

import os
import re
import threading
from pathlib import Path

from shesha import Shesha
from shesha.parser import create_default_registry
from shesha.project import Project
from shesha.storage.filesystem import FilesystemStorage

_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def validate_project_id(project_id: str) -> str:
    project_id = project_id.strip()
    if not project_id:
        raise ValidationError("project_id is required")
    if not _PROJECT_ID_RE.fullmatch(project_id):
        raise ValidationError(
            "Invalid project_id. Use 1-128 chars: letters, numbers, dot, underscore, hyphen."
        )
    return project_id


def validate_question(question: str) -> str:
    question = question.strip()
    if not question:
        raise ValidationError("question is required")
    if len(question) > 20_000:
        raise ValidationError("question is too long (max 20,000 characters)")
    return question


class LibrarianCore:
    """Shared stateful wrapper around Shesha + storage utilities."""

    def __init__(
        self,
        *,
        storage_path: Path,
        model: str | None = None,
        api_key: str | None = None,
        pool_size: int | None = None,
        keep_raw_files: bool = True,
    ) -> None:
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._storage = FilesystemStorage(storage_path, keep_raw_files=keep_raw_files)
        self._parser_registry = create_default_registry()

        self._model = model if model is not None else os.environ.get("SHESHA_MODEL")
        self._api_key = api_key if api_key is not None else os.environ.get("SHESHA_API_KEY")
        self._pool_size = pool_size

        self._shesha_lock = threading.Lock()
        self._shesha: Shesha | None = None

    def list_projects(self) -> list[str]:
        return self._storage.list_projects()

    def create_project(self, project_id: str) -> None:
        project_id = validate_project_id(project_id)
        self._storage.create_project(project_id)

    def delete_project(self, project_id: str) -> None:
        project_id = validate_project_id(project_id)
        self._storage.delete_project(project_id)

    def upload(self, project_id: str, path: Path, *, recursive: bool = False) -> list[str]:
        project_id = validate_project_id(project_id)
        if not self._storage.project_exists(project_id):
            raise ValidationError(f"Project '{project_id}' does not exist")

        path = path.expanduser()
        if not path.exists():
            raise ValidationError(f"Path not found: {path}")
        if not path.is_file() and not path.is_dir():
            raise ValidationError(f"Path is not a file or directory: {path}")

        project = Project(
            project_id=project_id,
            storage=self._storage,
            parser_registry=self._parser_registry,
        )
        return project.upload(path, recursive=recursive)

    def _get_shesha(self) -> Shesha:
        if self._shesha is not None:
            return self._shesha
        with self._shesha_lock:
            if self._shesha is not None:
                return self._shesha
            self._shesha = Shesha(
                model=self._model,
                api_key=self._api_key,
                storage_path=self.storage_path,
                pool_size=self._pool_size,
            )
            return self._shesha

    def query(self, project_id: str, question: str) -> str:
        project_id = validate_project_id(project_id)
        question = validate_question(question)

        shesha = self._get_shesha()
        project = shesha.get_project(project_id)
        result = project.query(question)
        return result.answer
