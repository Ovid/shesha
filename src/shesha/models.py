"""Core data models for Shesha."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from shesha.project import Project


@dataclass
class ParsedDocument:
    """A parsed document ready for storage and querying."""

    name: str
    content: str
    format: str
    metadata: dict[str, str | int | float | bool]
    char_count: int
    parse_warnings: list[str] = field(default_factory=list)


@dataclass
class RepoProjectResult:
    """Result from create_project_from_repo()."""

    project: "Project"
    status: Literal["created", "unchanged", "updates_available"]
    files_ingested: int
    files_skipped: int = 0
    warnings: list[str] = field(default_factory=list)
