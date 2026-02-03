"""Path traversal protection utilities."""

from pathlib import Path


class PathTraversalError(Exception):
    """Raised when a path escape attempt is detected."""

    pass


def safe_path(base: Path, *parts: str) -> Path:
    """
    Safely join path parts, ensuring result stays under base.

    Args:
        base: The root directory that must contain the result
        *parts: Path components to join (from user input)

    Returns:
        Resolved absolute path guaranteed under base

    Raises:
        PathTraversalError: If the result escapes base directory
    """
    base = base.resolve()
    target = base.joinpath(*parts).resolve()

    if not target.is_relative_to(base):
        raise PathTraversalError(f"Path escapes base directory: {'/'.join(parts)}")
    return target


def sanitize_filename(name: str) -> str:
    """
    Sanitize a filename for safe filesystem storage.

    Removes/replaces: path separators, null bytes, leading dots.
    """
    # Remove null bytes
    name = name.replace("\x00", "")
    # Replace path separators
    name = name.replace("/", "_").replace("\\", "_")
    # Remove leading dots (hidden files)
    name = name.lstrip(".")
    # Fallback for empty result
    return name or "unnamed"
