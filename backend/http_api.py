from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from mimetypes import guess_type
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .api import KidsGameAPI
from .chat_bridge import load_history, poll_messages, send_chat_turn
from .runtime_bridge import agent_status, health, list_sessions


class KidsGameHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "KidsGameUtilitiesHTTP/0.1"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json(HTTPStatus.NO_CONTENT, None)

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_PATCH(self) -> None:  # noqa: N802
        self._dispatch("PATCH")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    @property
    def api(self) -> KidsGameAPI:
        return self.server.api  # type: ignore[attr-defined]

    def _dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        body = self._read_json_body() if method in {"POST", "PATCH"} else {}
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}

        try:
            if parsed.path.startswith("/uploads/") and method == "GET":
                self._send_upload(parsed.path)
                return
            if parsed.path == "/health" and method == "GET":
                self._send_json(HTTPStatus.OK, health())
                return
            if parsed.path == "/sessions" and method == "GET":
                self._send_json(HTTPStatus.OK, list_sessions())
                return
            if parsed.path.startswith("/agent-status/") and method == "GET":
                session_name = parsed.path.rsplit("/", 1)[-1]
                self._send_json(HTTPStatus.OK, agent_status(session_name))
                return
            if parsed.path in {"/api/bootstrap", "/bootstrap"} and method == "GET":
                payload = self.api.get_bootstrap(user_id=self._required(query, "userId"))
            elif parsed.path == "/api/prefs/active-project":
                payload = self._handle_active_project(method, query, body)
            elif parsed.path == "/api/prefs/trigger-mode":
                payload = self._handle_trigger_mode(method, query, body)
            elif parsed.path == "/api/projects" and method == "GET":
                payload = self.api.list_projects()
            elif parsed.path in {"/api/artifacts", "/artifacts"}:
                payload = self._handle_artifacts(method, query, body)
            elif parsed.path.startswith("/api/artifacts/") and method == "PATCH":
                artifact_id = parsed.path.rsplit("/", 1)[-1]
                payload = self.api.update_artifact(artifact_id, **body)
            elif parsed.path == "/api/reports":
                payload = self._handle_reports(method, query, body)
            elif parsed.path.startswith("/api/reports/") and method == "GET":
                report_id = parsed.path.rsplit("/", 1)[-1]
                payload = self.api.get_report(report_id)
            elif parsed.path == "/chat" and method == "POST":
                payload = self._handle_chat(body)
            elif parsed.path.startswith("/history/") and method == "GET":
                session_name = parsed.path.rsplit("/", 1)[-1]
                payload = self._handle_history(session_name, query)
            elif parsed.path.startswith("/poll/") and method == "GET":
                session_name = parsed.path.rsplit("/", 1)[-1]
                payload = poll_messages(session_name)
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": f"unknown route: {parsed.path}"})
                return
        except KeyError as exc:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": str(exc)})
            return
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:  # pragma: no cover - defensive fallback
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
            return

        self._send_json(HTTPStatus.OK, payload)

    def _handle_active_project(self, method: str, query: dict[str, str], body: dict) -> dict:
        if method == "GET":
            return self.api.get_active_project(user_id=self._required(query, "userId"))
        if method == "POST":
            return self.api.set_active_project(
                user_id=self._required(body, "userId"),
                project_slug=body.get("projectSlug"),
            )
        raise ValueError(f"unsupported method: {method}")

    def _handle_trigger_mode(self, method: str, query: dict[str, str], body: dict) -> dict:
        if method == "GET":
            return self.api.get_trigger_mode(user_id=self._required(query, "userId"))
        if method == "POST":
            return self.api.set_trigger_mode(
                user_id=self._required(body, "userId"),
                mode=self._required(body, "mode"),
            )
        raise ValueError(f"unsupported method: {method}")

    def _handle_artifacts(self, method: str, query: dict[str, str], body: dict) -> dict:
        if method == "GET":
            include_deleted = query.get("includeDeleted", "false").lower() == "true"
            return self.api.list_artifacts(
                project_slug=query.get("projectSlug"),
                include_deleted=include_deleted,
                status=query.get("status"),
                linked_report_id=query.get("linkedReportId"),
            )
        if method == "POST":
            if body.get("image_b64") or body.get("imageBase64"):
                return self.api.upload_artifact(
                    image_b64=self._required_any(body, "image_b64", "imageBase64"),
                    image_filename=self._required_any(body, "image_filename", "imageFilename"),
                    label=self._required(body, "label"),
                    project_slug=body.get("projectSlug") or body.get("project_slug"),
                    mime_type=body.get("mimeType", "image/png"),
                    description=body.get("description"),
                    status=body.get("status", "accepted"),
                )
            return self.api.create_artifact(
                kind=self._required(body, "kind"),
                path=self._required(body, "path"),
                label=self._required(body, "label"),
                project_slug=body.get("projectSlug"),
                status=body.get("status", "suggested"),
                description=body.get("description"),
                mime_type=body.get("mimeType"),
            )
        raise ValueError(f"unsupported method: {method}")

    def _send_upload(self, request_path: str) -> None:
        relative = request_path.lstrip("/")
        target = (self.server.api.store.state_dir / relative).resolve()  # type: ignore[attr-defined]
        uploads_root = self.server.api.store.uploads_dir.resolve()  # type: ignore[attr-defined]
        if uploads_root not in target.parents and target != uploads_root:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "forbidden path"})
            return
        if not target.exists() or not target.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "upload not found"})
            return
        data = target.read_bytes()
        mime, _ = guess_type(str(target))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _handle_reports(self, method: str, query: dict[str, str], body: dict) -> dict:
        if method == "GET":
            return self.api.list_reports(project_slug=query.get("projectSlug"))
        if method == "POST":
            return self.api.create_or_update_report(
                report_id=body.get("id"),
                project_slug=self._required(body, "projectSlug"),
                title=self._required(body, "title"),
                markdown=self._required(body, "markdown"),
                artifact_ids=list(body.get("artifactIds") or []),
            )
        raise ValueError(f"unsupported method: {method}")

    def _handle_chat(self, body: dict) -> dict:
        return send_chat_turn(text=self._required(body, "text"), session=body.get("session"))

    def _handle_history(self, session_name: str, query: dict[str, str]) -> dict:
        limit = int(query.get("limit", "50"))
        messages = load_history(session_name, limit=limit)
        return {"messages": messages, "total": len(messages), "has_more": False}

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _required(self, source: dict, key: str) -> str:
        value = source.get(key)
        if value is None or value == "":
            raise ValueError(f"missing required field: {key}")
        return str(value)

    def _required_any(self, source: dict, *keys: str) -> str:
        for key in keys:
            value = source.get(key)
            if value is not None and value != "":
                return str(value)
        joined = ", ".join(keys)
        raise ValueError(f"missing required field: one of {joined}")

    def _send_json(self, status: HTTPStatus, payload: dict | None) -> None:
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PATCH,OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)


class KidsGameHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], root: str | Path):
        super().__init__(server_address, KidsGameHTTPRequestHandler)
        self.api = KidsGameAPI(root)


def run_http_server(*, root: str | Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    server = KidsGameHTTPServer((host, port), root)
    try:
        server.serve_forever()
    finally:
        server.server_close()
