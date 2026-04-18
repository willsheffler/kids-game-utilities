from __future__ import annotations

import json
import os
import pathlib
import socket
from typing import Any

from harness.core import DEFAULT_SOCKET_PATH as HARNESS_DEFAULT_SOCKET_PATH

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[3]
REGISTRY_PATH = WORKSPACE_ROOT / "harness" / "agent_registry.json"
DEFAULT_BACKEND_TARGET = os.environ.get("KIDS_GAME_UTILITIES_DEFAULT_BACKEND", "media-madeira")


def _send_harness_command(payload: dict[str, Any], *, timeout_s: float = 3.0) -> dict[str, Any]:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(timeout_s)
    try:
        client.connect(HARNESS_DEFAULT_SOCKET_PATH)
        client.sendall(json.dumps(payload).encode("utf-8"))
        client.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            data = client.recv(65536)
            if not data:
                break
            chunks.append(data)
    finally:
        client.close()
    return json.loads(b"".join(chunks).decode("utf-8"))


def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "default_session": DEFAULT_BACKEND_TARGET,
        "user": os.environ.get("USER", "unknown"),
        "host": os.uname().nodename,
    }


def list_sessions() -> dict[str, Any]:
    sessions = []
    try:
        payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        for agent in payload.get("agents", []):
            session = agent.get("session")
            if session:
                sessions.append(session)
    except Exception:
        if DEFAULT_BACKEND_TARGET:
            sessions.append(DEFAULT_BACKEND_TARGET)
    unique = sorted(set(sessions))
    return {"sessions": unique, "default": DEFAULT_BACKEND_TARGET}


def agent_status(session_name: str) -> dict[str, Any]:
    try:
        result = _send_harness_command(
            {"command": "inspect-target-pane", "target": session_name},
            timeout_s=3.0,
        )
        payload = result.get("result") or {}
        return {
            "session": session_name,
            "pane_command": payload.get("pane_command") or payload.get("current_command") or "",
            "status": payload.get("status") or "unknown",
            "busy_status": payload.get("busy_status"),
            "last_line": str(payload.get("last_line") or "")[-80:],
            "runtime_family": payload.get("runtime_family"),
            "logical_actor": payload.get("logical_actor"),
            "role_kind": payload.get("role_kind"),
            "status_reason": payload.get("status_reason"),
            "prompt_visible": payload.get("prompt_visible"),
        }
    except Exception as exc:
        return {"session": session_name, "status": "unknown", "error": str(exc)}
