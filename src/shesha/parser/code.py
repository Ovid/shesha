"""Code file parser for source code files."""

from pathlib import Path

from shesha.storage.base import ParsedDocument

# Map extensions to language names
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".cs": "csharp",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".sql": "sql",
    ".r": "r",
    ".R": "r",
}


class CodeParser:
    """Parser for source code files."""

    def can_parse(self, path: Path, mime_type: str | None = None) -> bool:
        """Check if this parser can handle the given file."""
        return path.suffix.lower() in EXTENSION_TO_LANGUAGE

    def parse(self, path: Path) -> ParsedDocument:
        """Parse a code file and return a ParsedDocument."""
        content = path.read_text(encoding="utf-8")
        ext = path.suffix.lower()
        language = EXTENSION_TO_LANGUAGE.get(ext, "unknown")

        return ParsedDocument(
            name=path.name,
            content=content,
            format=ext.lstrip("."),
            metadata={"language": language, "encoding": "utf-8"},
            char_count=len(content),
            parse_warnings=[],
        )
