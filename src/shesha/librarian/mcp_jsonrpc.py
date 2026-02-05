"""Minimal JSON-RPC framing helpers for MCP over stdio.

MCP stdio uses JSON-RPC messages framed with LSP-style `Content-Length` headers.
This module keeps the framing and parsing logic small and dependency-free so we
can self-test the server during install.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any, BinaryIO


class JsonRpcProtocolError(RuntimeError):
    """Raised for invalid framing or malformed JSON-RPC messages."""


def encode_message(message: Mapping[str, Any]) -> bytes:
    """Encode a JSON-RPC message with `Content-Length` framing."""
    payload = json.dumps(dict(message), separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
    return header + payload


def parse_messages(data: bytes) -> list[dict[str, Any]]:
    """Parse one or more framed JSON-RPC messages from `data`."""
    messages: list[dict[str, Any]] = []
    i = 0

    while i < len(data):
        header_end = data.find(b"\r\n\r\n", i)
        if header_end == -1:
            raise JsonRpcProtocolError("Incomplete message headers")

        header_text = data[i:header_end].decode("ascii", errors="replace")
        headers: dict[str, str] = {}
        for line in header_text.split("\r\n"):
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        if "content-length" not in headers:
            raise JsonRpcProtocolError("Missing Content-Length header")
        try:
            length = int(headers["content-length"])
        except ValueError as e:
            raise JsonRpcProtocolError("Invalid Content-Length header") from e
        if length < 0:
            raise JsonRpcProtocolError("Negative Content-Length")

        body_start = header_end + 4
        body_end = body_start + length
        if body_end > len(data):
            raise JsonRpcProtocolError("Incomplete message body")

        body = data[body_start:body_end]
        try:
            msg = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise JsonRpcProtocolError("Invalid JSON body") from e
        if not isinstance(msg, dict):
            raise JsonRpcProtocolError("JSON-RPC message must be an object")

        messages.append(msg)
        i = body_end

    return messages


def _read_exact(stream: BinaryIO, n: int, *, timeout_sec: float | None) -> bytes:
    deadline = time.monotonic() + timeout_sec if timeout_sec is not None else None
    buf = bytearray()
    while len(buf) < n:
        if deadline is not None and time.monotonic() > deadline:
            raise TimeoutError(f"Timed out reading {n} bytes")
        chunk = stream.read(n - len(buf))
        if not chunk:
            raise EOFError("EOF while reading message body")
        buf.extend(chunk)
    return bytes(buf)


def _read_until(stream: BinaryIO, marker: bytes, *, timeout_sec: float | None) -> bytes:
    deadline = time.monotonic() + timeout_sec if timeout_sec is not None else None
    buf = bytearray()
    while True:
        if deadline is not None and time.monotonic() > deadline:
            raise TimeoutError("Timed out reading message headers")
        chunk = stream.read(1)
        if not chunk:
            raise EOFError("EOF while reading message headers")
        buf.extend(chunk)
        if buf.endswith(marker):
            return bytes(buf)


def read_message(stream: BinaryIO, *, timeout_sec: float | None = None) -> dict[str, Any]:
    """Read a single framed JSON-RPC message from `stream`."""
    header_bytes = _read_until(stream, b"\r\n\r\n", timeout_sec=timeout_sec)
    header_text = header_bytes.decode("ascii", errors="replace")
    headers: dict[str, str] = {}
    for line in header_text.split("\r\n"):
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()

    if "content-length" not in headers:
        raise JsonRpcProtocolError("Missing Content-Length header")
    try:
        length = int(headers["content-length"])
    except ValueError as e:
        raise JsonRpcProtocolError("Invalid Content-Length header") from e
    if length < 0:
        raise JsonRpcProtocolError("Negative Content-Length")

    body = _read_exact(stream, length, timeout_sec=timeout_sec)
    try:
        msg = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise JsonRpcProtocolError("Invalid JSON body") from e
    if not isinstance(msg, dict):
        raise JsonRpcProtocolError("JSON-RPC message must be an object")
    return msg


def write_message(stream: BinaryIO, message: Mapping[str, Any]) -> None:
    """Write a framed JSON-RPC message to `stream`."""
    stream.write(encode_message(message))
    stream.flush()
