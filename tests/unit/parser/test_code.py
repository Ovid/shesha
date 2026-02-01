"""Tests for code file parser."""

from pathlib import Path

import pytest

from shesha.parser.code import CodeParser


@pytest.fixture
def parser() -> CodeParser:
    return CodeParser()


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent.parent.parent / "fixtures"


class TestCodeParser:
    """Tests for CodeParser."""

    def test_can_parse_python(self, parser: CodeParser):
        """CodeParser can parse .py files."""
        assert parser.can_parse(Path("test.py"))

    def test_can_parse_javascript(self, parser: CodeParser):
        """CodeParser can parse .js files."""
        assert parser.can_parse(Path("test.js"))

    def test_can_parse_typescript(self, parser: CodeParser):
        """CodeParser can parse .ts files."""
        assert parser.can_parse(Path("test.ts"))

    def test_cannot_parse_text(self, parser: CodeParser):
        """CodeParser doesn't handle plain text."""
        assert not parser.can_parse(Path("test.txt"))

    def test_parse_python_file(self, parser: CodeParser, fixtures_dir: Path):
        """CodeParser extracts Python code with language metadata."""
        doc = parser.parse(fixtures_dir / "sample.py")
        assert doc.name == "sample.py"
        assert "def hello" in doc.content
        assert doc.format == "py"
        assert doc.metadata["language"] == "python"

    def test_parse_javascript_file(self, parser: CodeParser, fixtures_dir: Path):
        """CodeParser extracts JavaScript code with language metadata."""
        doc = parser.parse(fixtures_dir / "sample.js")
        assert doc.name == "sample.js"
        assert "function hello" in doc.content
        assert doc.format == "js"
        assert doc.metadata["language"] == "javascript"
