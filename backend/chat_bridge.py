from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any

WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from harness.core import DEFAULT_SOCKET_PATH as HARNESS_DEFAULT_SOCKET_PATH
from harness.core import send_command as harness_send_command
CHATLOG_ROOT = pathlib.Path(
    os.environ.get("PENSIEVE_CHATLOG_ROOT", str(WORKSPACE_ROOT / "data" / "will" / "sources" / "chatlogs"))
)
FRONTEND_PUSH_ROOT = pathlib.Path(
    os.environ.get("PENSIEVE_FRONTEND_PUSH_ROOT", os.path.expanduser("~/.local/share/pensieve-harness/frontend_push"))
)
DEFAULT_BACKEND_TARGET = os.environ.get("KIDS_GAME_UTILITIES_DEFAULT_BACKEND", "media-madeira")
DEFAULT_SESSION_ID_PREFIX = "kgu"


def _session_id(backend_target: str) -> str:
    safe = backend_target.replace("/", "_").replace("..", "_")
    return f"{DEFAULT_SESSION_ID_PREFIX}_{safe}"


def send_chat_turn(*, text: str, session: str | None) -> dict[str, Any]:
    backend_target = (session or DEFAULT_BACKEND_TARGET).strip()
    if not backend_target:
        raise ValueError("session or default backend target required")
    payload = {
        "command": "frontend-turn",
        "sessionId": _session_id(backend_target),
        "backendTarget": backend_target,
        "text": text,
        "platform": "frontend_web",
        "surface": "web",
        "ttsEnabled": False,
        "userExtraAttributes": {"input_mode": "typed"},
    }
    resp = harness_send_command(HARNESS_DEFAULT_SOCKET_PATH, payload, wait_timeout_s=310.0)
    if not resp.get("ok"):
        raise RuntimeError(resp.get("error", "frontend-turn failed"))
    result = resp.get("result") or {}
    if not result.get("ok", False):
        raise RuntimeError(result.get("issue") or "frontend-turn failed")
    return {
        "backendTarget": backend_target,
        "sessionId": payload["sessionId"],
        "reply": result.get("reply_text", ""),
        "turnId": result.get("turn_id"),
    }


def _parse_chatlog_file(filepath: pathlib.Path) -> list[dict]:
    messages = []
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return []
    for block in re.split(r"(?=<message\b)", text):
        if not block.strip().startswith("<message"):
            continue
        direction = re.search(r'direction="(\w+)"', block)
        ts = re.search(r'ts_local="([^"]+)"', block)
        payload_match = re.search(r"<payload>\s*(.*?)\s*</payload>", block, re.DOTALL)
        if not direction or not payload_match:
            continue
        role = "user" if direction.group(1) == "in" else "agent"
        ts_str = ""
        if ts:
            try:
                parsed = dt.datetime.strptime(ts.group(1).split(" America")[0].split(" US")[0].strip(), "%Y-%m-%d %H:%M:%S")
                ts_str = parsed.strftime("%m/%d %H:%M")
            except Exception:
                ts_str = ts.group(1)[:11]
        messages.append({"role": role, "text": payload_match.group(1).strip(), "ts": ts_str})
    return messages


def load_history(session: str, *, limit: int = 50) -> list[dict]:
    safe = (session or "").replace("/", "_").replace("..", "_")
    if not safe:
        return []
    safe_underscore = safe.replace("-", "_")
    messages: list[dict] = []
    date_dirs = sorted(CHATLOG_ROOT.glob("????/??/??/frontend_web"), reverse=True)
    for date_dir in date_dirs[:7]:
        files = sorted(date_dir.glob(f"*{safe_underscore}*.xmlish"), reverse=True)
        for file in files:
            if "push_" in file.name:
                continue
            messages = _parse_chatlog_file(file) + messages
            if len(messages) >= limit:
                break
        if len(messages) >= limit:
            break
    messages.sort(key=lambda m: m.get("ts", ""))
    return messages[-limit:]


def _read_and_consume_spool(session_name: str) -> list[dict]:
    safe = session_name.strip()
    if not safe or "/" in safe or "\\" in safe:
        return []
    session_dir = FRONTEND_PUSH_ROOT / safe
    if not session_dir.is_dir():
        return []
    messages = []
    for file in sorted(session_dir.glob("*.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            messages.append(
                {
                    "role": "agent",
                    "text": data.get("text", ""),
                    "sender": data.get("sender", ""),
                    "message_type": data.get("message_type", "info"),
                    "importance": data.get("importance", "normal"),
                    "id": data.get("id", ""),
                    "ts": data.get("ts", ""),
                }
            )
            file.unlink()
        except Exception:
            continue
    return messages


def poll_messages(session_name: str) -> dict[str, Any]:
    messages = _read_and_consume_spool(session_name)
    pending_sessions = []
    if FRONTEND_PUSH_ROOT.is_dir():
        for entry in FRONTEND_PUSH_ROOT.iterdir():
            if entry.is_dir() and any(entry.glob("*.json")):
                pending_sessions.append(entry.name)
    return {"messages": messages, "pending_sessions": sorted(set(pending_sessions))}
