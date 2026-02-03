"""Tests for path traversal protection."""

from pathlib import Path

import pytest

from shesha.security.paths import PathTraversalError, safe_path, sanitize_filename


class TestSafePath:
    """Tests for safe_path function."""

    def test_simple_path_under_base(self, tmp_path: Path) -> None:
        """Simple path stays under base."""
        result = safe_path(tmp_path, "subdir", "file.txt")
        assert result == tmp_path / "subdir" / "file.txt"

    def test_traversal_with_dotdot_raises(self, tmp_path: Path) -> None:
        """Path with .. that escapes base raises error."""
        with pytest.raises(PathTraversalError):
            safe_path(tmp_path, "..", "escape.txt")

    def test_traversal_in_middle_raises(self, tmp_path: Path) -> None:
        """Path with .. in middle that escapes raises error."""
        with pytest.raises(PathTraversalError):
            safe_path(tmp_path, "subdir", "..", "..", "escape.txt")

    def test_dotdot_staying_in_base_ok(self, tmp_path: Path) -> None:
        """Path with .. that stays under base is allowed."""
        result = safe_path(tmp_path, "subdir", "..", "other.txt")
        assert result == tmp_path / "other.txt"

    def test_absolute_path_escape_raises(self, tmp_path: Path) -> None:
        """Absolute path component raises if it escapes."""
        with pytest.raises(PathTraversalError):
            safe_path(tmp_path, "/etc/passwd")


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_normal_filename_unchanged(self) -> None:
        """Normal filename passes through."""
        assert sanitize_filename("document.txt") == "document.txt"

    def test_removes_null_bytes(self) -> None:
        """Null bytes are removed."""
        assert sanitize_filename("file\x00name.txt") == "filename.txt"

    def test_replaces_forward_slash(self) -> None:
        """Forward slashes become underscores."""
        assert sanitize_filename("path/to/file.txt") == "path_to_file.txt"

    def test_replaces_backslash(self) -> None:
        """Backslashes become underscores."""
        assert sanitize_filename("path\\to\\file.txt") == "path_to_file.txt"

    def test_strips_leading_dots(self) -> None:
        """Leading dots are stripped."""
        assert sanitize_filename("..hidden") == "hidden"
        assert sanitize_filename(".hidden") == "hidden"

    def test_empty_becomes_unnamed(self) -> None:
        """Empty string becomes 'unnamed'."""
        assert sanitize_filename("") == "unnamed"

    def test_only_dots_becomes_unnamed(self) -> None:
        """String of only dots becomes 'unnamed'."""
        assert sanitize_filename("...") == "unnamed"
