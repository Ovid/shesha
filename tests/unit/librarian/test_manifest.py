"""Tests for Librarian manifest writing."""

import json
from pathlib import Path

from shesha.librarian.manifest import LibrarianManifest, SelfTestStatus


def test_manifest_round_trip(tmp_path: Path) -> None:
    """Manifest can be written and read back with required metadata."""
    manifest_path = tmp_path / "manifest.json"
    manifest = LibrarianManifest(
        package_name="shesha",
        package_version="0.0.0",
        entrypoints={"cli": "/bin/cli", "mcp": "/bin/mcp"},
        commands={"cli": ["/bin/cli"], "mcp": ["/bin/mcp"]},
        storage_path=str(tmp_path / "storage"),
        logs_path=str(tmp_path / "logs"),
        supported_modes=["cli", "mcp"],
        env_vars=[
            "LIBRARIAN_HOME",
            "LIBRARIAN_STORAGE_PATH",
            "LIBRARIAN_LOG_DIR",
        ],
        self_test=SelfTestStatus(ok=True, timestamp="2026-02-05T00:00:00Z", details="ok"),
    )

    manifest.write(manifest_path)
    loaded = LibrarianManifest.read(manifest_path)

    assert loaded.package_name == "shesha"
    assert loaded.entrypoints["mcp"] == "/bin/mcp"
    assert loaded.commands["mcp"] == ["/bin/mcp"]
    assert loaded.supported_modes == ["cli", "mcp"]

    # Basic JSON validity check
    raw = json.loads(manifest_path.read_text())
    assert raw["package"]["name"] == "shesha"
    assert raw["commands"]["cli"] == ["/bin/cli"]
    assert "self_test" in raw
