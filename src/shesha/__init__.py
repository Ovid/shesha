"""Shesha: Recursive Language Models for document querying."""

from shesha.exceptions import (
    DocumentError,
    DocumentNotFoundError,
    NoParserError,
    ParseError,
    ProjectError,
    ProjectExistsError,
    ProjectNotFoundError,
    SheshaError,
)
from shesha.models import ParsedDocument
from shesha.storage import FilesystemStorage

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Storage
    "FilesystemStorage",
    "ParsedDocument",
    # Exceptions
    "SheshaError",
    "ProjectError",
    "ProjectNotFoundError",
    "ProjectExistsError",
    "DocumentError",
    "DocumentNotFoundError",
    "ParseError",
    "NoParserError",
]
