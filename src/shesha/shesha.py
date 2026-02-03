"""Main Shesha class - the public API."""

import atexit
import re
import weakref
from pathlib import Path
from typing import TYPE_CHECKING

from shesha.config import SheshaConfig
from shesha.models import ParsedDocument, RepoProjectResult
from shesha.parser import create_default_registry
from shesha.project import Project
from shesha.repo.ingester import RepoIngester
from shesha.rlm.engine import RLMEngine
from shesha.sandbox.pool import ContainerPool
from shesha.storage.filesystem import FilesystemStorage

if TYPE_CHECKING:
    from shesha.parser.base import DocumentParser


class Shesha:
    """Main entry point for Shesha - Recursive Language Models."""

    def __init__(
        self,
        model: str | None = None,
        storage_path: str | Path | None = None,
        api_key: str | None = None,
        pool_size: int | None = None,
        config: SheshaConfig | None = None,
    ) -> None:
        """Initialize Shesha."""
        # Use provided config or create from args
        if config is None:
            config = SheshaConfig()
        if model is not None:
            config.model = model
        if storage_path is not None:
            config.storage_path = str(storage_path)
        if api_key is not None:
            config.api_key = api_key
        if pool_size is not None:
            config.pool_size = pool_size

        self._config = config

        # Initialize components
        self._storage = FilesystemStorage(
            config.storage_path,
            keep_raw_files=config.keep_raw_files,
        )
        self._parser_registry = create_default_registry()
        self._pool = ContainerPool(
            size=config.pool_size,
            image=config.sandbox_image,
            memory_limit=f"{config.container_memory_mb}m",
        )

        # Create RLM engine
        self._rlm_engine = RLMEngine(
            model=config.model,
            api_key=config.api_key,
            max_iterations=config.max_iterations,
            max_output_chars=config.max_output_chars,
            execution_timeout=config.execution_timeout_sec,
        )

        # Initialize repo ingester
        self._repo_ingester = RepoIngester(storage_path=config.storage_path)

        # Track if stopped to avoid double-cleanup
        self._stopped = False

        # Register cleanup on exit using weak reference
        weak_self = weakref.ref(self)

        def _cleanup() -> None:
            obj = weak_self()
            if obj is not None:
                obj.stop()

        atexit.register(_cleanup)

    def create_project(self, project_id: str) -> Project:
        """Create a new project."""
        self._storage.create_project(project_id)
        return Project(
            project_id=project_id,
            storage=self._storage,
            parser_registry=self._parser_registry,
            rlm_engine=self._rlm_engine,
        )

    def get_project(self, project_id: str) -> Project:
        """Get an existing project."""
        if not self._storage.project_exists(project_id):
            raise ValueError(f"Project '{project_id}' does not exist")
        return Project(
            project_id=project_id,
            storage=self._storage,
            parser_registry=self._parser_registry,
            rlm_engine=self._rlm_engine,
        )

    def list_projects(self) -> list[str]:
        """List all projects."""
        return self._storage.list_projects()

    def delete_project(self, project_id: str) -> None:
        """Delete a project."""
        self._storage.delete_project(project_id)

    def register_parser(self, parser: "DocumentParser") -> None:
        """Register a custom document parser."""
        self._parser_registry.register(parser)

    def start(self) -> None:
        """Start the container pool."""
        self._stopped = False
        self._pool.start()

    def stop(self) -> None:
        """Stop the container pool."""
        if self._stopped:
            return
        self._stopped = True
        self._pool.stop()

    def __enter__(self) -> "Shesha":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.stop()

    def create_project_from_repo(
        self,
        url: str,
        name: str | None = None,
        token: str | None = None,
        path: str | None = None,
    ) -> RepoProjectResult:
        """Create a project from a git repository.

        Args:
            url: Git URL (HTTPS, SSH) or local path.
            name: Project name (defaults to repo name).
            token: Auth token (defaults to env var based on host).
            path: Optional subdirectory to ingest.

        Returns:
            RepoProjectResult with project and status.
        """
        if name is None:
            name = self._extract_repo_name(url)

        resolved_token = self._repo_ingester.resolve_token(url, token)

        if self._storage.project_exists(name):
            return self._handle_existing_project(url, name, resolved_token, path)

        return self._create_new_project_from_repo(url, name, resolved_token, path)

    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL."""
        if self._repo_ingester.is_local_path(url):
            return Path(url).expanduser().name
        match = re.search(r"[/:]([^/]+/[^/]+?)(?:\.git)?$", url)
        if match:
            return match.group(1).replace("/", "-")
        return "unnamed-repo"

    def _handle_existing_project(
        self,
        url: str,
        name: str,
        token: str | None,
        path: str | None,
    ) -> RepoProjectResult:
        """Handle create_project_from_repo for existing project."""
        saved_sha = self._repo_ingester.get_saved_sha(name)
        if self._repo_ingester.is_local_path(url):
            current_sha = self._repo_ingester.get_local_sha(name)
        else:
            current_sha = self._repo_ingester.get_remote_sha(url, token)

        project = self.get_project(name)

        if saved_sha == current_sha:
            return RepoProjectResult(
                project=project,
                status="unchanged",
                files_ingested=len(self._storage.list_documents(name)),
            )

        def apply_updates() -> RepoProjectResult:
            self._repo_ingester.pull(name)
            return self._ingest_repo(url, name, token, path, is_update=True)

        return RepoProjectResult(
            project=project,
            status="updates_available",
            files_ingested=len(self._storage.list_documents(name)),
            _apply_updates_fn=apply_updates,
        )

    def _create_new_project_from_repo(
        self,
        url: str,
        name: str,
        token: str | None,
        path: str | None,
    ) -> RepoProjectResult:
        """Create a new project from repo."""
        if not self._repo_ingester.is_local_path(url):
            self._repo_ingester.clone(url, name, token)
        return self._ingest_repo(url, name, token, path, is_update=False)

    def _ingest_repo(
        self,
        url: str,
        name: str,
        token: str | None,
        path: str | None,
        *,
        is_update: bool,
    ) -> RepoProjectResult:
        """Ingest files from repository into project."""
        if not is_update:
            self._storage.create_project(name)

        if self._repo_ingester.is_local_path(url):
            repo_path = Path(url).expanduser()
        else:
            repo_path = self._repo_ingester.repos_dir / name

        files = self._repo_ingester.list_files(name, subdir=path)
        files_ingested = 0
        files_skipped = 0
        warnings: list[str] = []

        for file_path in files:
            full_path = repo_path / file_path
            try:
                parser = self._parser_registry.find_parser(full_path)
                if parser is None:
                    files_skipped += 1
                    continue

                doc = parser.parse(full_path, include_line_numbers=True, file_path=file_path)
                doc = ParsedDocument(
                    name=file_path,
                    content=doc.content,
                    format=doc.format,
                    metadata=doc.metadata,
                    char_count=doc.char_count,
                    parse_warnings=doc.parse_warnings,
                )
                self._storage.store_document(name, doc)
                files_ingested += 1
            except Exception as e:
                files_skipped += 1
                warnings.append(f"Failed to parse {file_path}: {e}")

        sha = self._repo_ingester.get_local_sha(name)
        if sha:
            self._repo_ingester.save_sha(name, sha)

        project = self.get_project(name)
        return RepoProjectResult(
            project=project,
            status="created",
            files_ingested=files_ingested,
            files_skipped=files_skipped,
            warnings=warnings,
        )
