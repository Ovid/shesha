"""Core data models for Shesha."""

from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    """A parsed document ready for storage and querying."""

    name: str
    content: str
    format: str
    metadata: dict[str, str | int | float | bool]
    char_count: int
    parse_warnings: list[str] = field(default_factory=list)
