"""MCP stdio server for Librarian (Shesha RLM).

This is a minimal MCP implementation over stdio (JSON-RPC 2.0 with
`Content-Length` framing). It intentionally avoids assuming any specific client.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shesha import __version__
from shesha.librarian.core import LibrarianCore, ValidationError
from shesha.librarian.mcp_jsonrpc import JsonRpcProtocolError, read_message, write_message
from shesha.librarian.paths import resolve_paths

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "Librarian"


@dataclass(frozen=True)
class ToolDef:
    name: str
    description: str
    input_schema: dict[str, Any]


def _tool_defs() -> list[ToolDef]:
    return [
        ToolDef(
            name="health",
            description="Basic server health check (includes docker status).",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
        ToolDef(
            name="projects_list",
            description="List known project IDs.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
        ToolDef(
            name="project_create",
            description="Create a new project.",
            input_schema={
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "required": ["project_id"],
                "additionalProperties": False,
            },
        ),
        ToolDef(
            name="project_delete",
            description="Delete a project and its documents.",
            input_schema={
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "required": ["project_id"],
                "additionalProperties": False,
            },
        ),
        ToolDef(
            name="project_upload",
            description="Upload a file or directory into a project.",
            input_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "path": {"type": "string"},
                    "recursive": {"type": "boolean", "default": False},
                },
                "required": ["project_id", "path"],
                "additionalProperties": False,
            },
        ),
        ToolDef(
            name="project_query",
            description="Query a project using Shesha RLM (requires docker + LLM credentials).",
            input_schema={
                "type": "object",
                "properties": {"project_id": {"type": "string"}, "question": {"type": "string"}},
                "required": ["project_id", "question"],
                "additionalProperties": False,
            },
        ),
    ]


def _jsonrpc_response(id_value: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_value, "result": result}


def _jsonrpc_error(id_value: Any, code: int, message: str, *, data: Any = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_value, "error": err}


def _content_text(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _handle_tools_call(core: LibrarianCore, params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    args = params.get("arguments") or {}
    if not isinstance(name, str):
        raise ValidationError("tools/call params.name must be a string")
    if not isinstance(args, dict):
        raise ValidationError("tools/call params.arguments must be an object")

    if name == "health":
        docker_ok = True
        docker_error: str | None = None
        try:
            # Call through Shesha's own check for consistent messaging.
            from shesha.shesha import Shesha as SheshaClass

            SheshaClass._check_docker_available()
        except Exception as e:  # noqa: BLE001 - surfaced as status, not swallowed
            docker_ok = False
            docker_error = str(e)

        payload = {
            "status": "ok",
            "server": {"name": SERVER_NAME, "version": __version__},
            "storage_path": str(core.storage_path),
            "docker": {"ok": docker_ok, "error": docker_error},
        }
        return _content_text(json.dumps(payload, indent=2))

    if name == "projects_list":
        return _content_text(json.dumps({"projects": core.list_projects()}, indent=2))

    if name == "project_create":
        project_id = str(args.get("project_id", ""))
        core.create_project(project_id)
        return _content_text(json.dumps({"status": "created", "project_id": project_id}, indent=2))

    if name == "project_delete":
        project_id = str(args.get("project_id", ""))
        core.delete_project(project_id)
        return _content_text(json.dumps({"status": "deleted", "project_id": project_id}, indent=2))

    if name == "project_upload":
        project_id = str(args.get("project_id", ""))
        path = Path(str(args.get("path", ""))).expanduser()
        recursive = bool(args.get("recursive", False))
        uploaded = core.upload(project_id, path, recursive=recursive)
        return _content_text(json.dumps({"uploaded": uploaded}, indent=2))

    if name == "project_query":
        project_id = str(args.get("project_id", ""))
        question = str(args.get("question", ""))
        answer = core.query(project_id, question)
        return _content_text(answer)

    raise ValidationError(f"Unknown tool: {name}")


def serve(core: LibrarianCore) -> int:
    """Run the MCP server loop (stdio)."""
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        try:
            msg = read_message(stdin)
        except EOFError:
            return 0
        except TimeoutError:
            continue
        except JsonRpcProtocolError as e:
            # Protocol errors are fatal; there's no reliable way to recover framing.
            write_message(stdout, _jsonrpc_error(None, -32700, f"Protocol error: {e}"))
            return 1

        method = msg.get("method")
        msg_id = msg.get("id")
        respond = msg_id is not None

        # Ignore non-request messages
        if not isinstance(method, str):
            continue

        params = msg.get("params") or {}
        if params is None:
            params = {}
        if not isinstance(params, dict):
            params = {}

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": SERVER_NAME, "version": __version__},
                }
                if respond:
                    write_message(stdout, _jsonrpc_response(msg_id, result))
                continue

            if method == "tools/list":
                tools = [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.input_schema,
                    }
                    for t in _tool_defs()
                ]
                if respond:
                    write_message(stdout, _jsonrpc_response(msg_id, {"tools": tools}))
                continue

            if method == "tools/call":
                result = _handle_tools_call(core, params)
                if respond:
                    write_message(stdout, _jsonrpc_response(msg_id, result))
                continue

            if method == "shutdown":
                if respond:
                    write_message(stdout, _jsonrpc_response(msg_id, {}))
                return 0

            if respond:
                write_message(stdout, _jsonrpc_error(msg_id, -32601, f"Method not found: {method}"))

        except ValidationError as e:
            if respond:
                write_message(stdout, _jsonrpc_error(msg_id, -32602, str(e)))
        except Exception as e:  # noqa: BLE001 - surface safe error + details for operator
            # Avoid leaking internal details unless explicitly requested; keep traceback in stderr.
            traceback.print_exc(file=sys.stderr)
            if respond:
                write_message(stdout, _jsonrpc_error(msg_id, -32603, f"Internal error: {e}"))


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="librarian-mcp",
        description="Run Librarian as an MCP server (stdio).",
    )
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=None,
        help="Override storage directory (default: LIBRARIAN_STORAGE_PATH or LIBRARIAN_HOME).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Override log directory (default: LIBRARIAN_LOG_DIR or LIBRARIAN_HOME).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override SHESHA_MODEL for queries.",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Override SHESHA_API_KEY for queries.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    paths = resolve_paths()
    storage_path = args.storage_path if args.storage_path is not None else paths.storage
    logs_path = args.log_dir if args.log_dir is not None else paths.logs
    storage_path.mkdir(parents=True, exist_ok=True)
    logs_path.mkdir(parents=True, exist_ok=True)

    core = LibrarianCore(storage_path=storage_path, model=args.model, api_key=args.api_key)
    return serve(core)


if __name__ == "__main__":
    raise SystemExit(main())
