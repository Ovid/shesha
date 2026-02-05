"""Tests for Librarian MCP stdio server."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from shesha.librarian.mcp_jsonrpc import encode_message, parse_messages


def test_mcp_server_initializes_and_reports_health(tmp_path: Path) -> None:
    """Server starts and answers health tool call without requiring an LLM."""
    storage_path = tmp_path / "storage"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "shesha.librarian.mcp",
            "--storage-path",
            str(storage_path),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    try:
        input_data = b"".join(
            [
                encode_message(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "0.0"},
                        },
                    }
                ),
                encode_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
                encode_message(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {"name": "health", "arguments": {}},
                    }
                ),
            ]
        )

        stdout, _stderr = proc.communicate(input=input_data, timeout=5)
        messages = parse_messages(stdout)

        init_resp = next(m for m in messages if m.get("id") == 1)
        assert init_resp["result"]["serverInfo"]["name"] == "Librarian"

        tools_resp = next(m for m in messages if m.get("id") == 2)
        tool_names = {t["name"] for t in tools_resp["result"]["tools"]}
        assert "health" in tool_names

        health_resp = next(m for m in messages if m.get("id") == 3)
        content = health_resp["result"]["content"]
        assert content and content[0]["type"] == "text"
        assert "ok" in content[0]["text"].lower()
    finally:
        if proc.poll() is None:
            proc.kill()


def test_mcp_server_ignores_notifications(tmp_path: Path) -> None:
    """Server does not respond to JSON-RPC notifications (no id)."""
    storage_path = tmp_path / "storage"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "shesha.librarian.mcp",
            "--storage-path",
            str(storage_path),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None

    try:
        input_data = b"".join(
            [
                encode_message(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "0.0"},
                        },
                    }
                ),
                encode_message(
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {},
                    }
                ),
            ]
        )
        stdout, _stderr = proc.communicate(input=input_data, timeout=5)
        messages = parse_messages(stdout)
        assert [m.get("id") for m in messages] == [1]
    finally:
        if proc.poll() is None:
            proc.kill()
