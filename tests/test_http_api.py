from __future__ import annotations

import base64
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest.mock import patch

from backend.http_api import KidsGameHTTPServer


class KidsGameHTTPAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server = KidsGameHTTPServer(("127.0.0.1", 0), self.tmp.name)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._cleanup_server)
        host, port = self.server.server_address
        self.base = f"http://{host}:{port}"

    def _cleanup_server(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(f"{self.base}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, json.loads(exc.read().decode("utf-8"))
            finally:
                exc.close()

    def test_http_bootstrap_returns_json_payload(self):
        self.request("POST", "/api/prefs/active-project", {"userId": "will", "projectSlug": "tower-defense"})
        status, payload = self.request("GET", "/api/bootstrap?userId=will")
        self.assertEqual(200, status)
        self.assertEqual("tower-defense", payload["result"]["prefs"]["activeProject"])

    def test_http_trigger_mode_round_trip(self):
        status, payload = self.request("POST", "/api/prefs/trigger-mode", {"userId": "will", "mode": "manual"})
        self.assertEqual(200, status)
        self.assertEqual("manual", payload["result"]["triggerMode"])
        status, payload = self.request("GET", "/api/prefs/trigger-mode?userId=will")
        self.assertEqual(200, status)
        self.assertEqual("manual", payload["result"]["triggerMode"])

    def test_http_artifact_create_list_and_patch(self):
        status, created = self.request(
            "POST",
            "/api/artifacts",
            {
                "kind": "screenshot",
                "path": "shots/one.png",
                "label": "one",
                "projectSlug": "tower-defense",
                "status": "suggested",
            },
        )
        self.assertEqual(200, status)
        artifact_id = created["result"]["artifact"]["id"]
        status, updated = self.request("PATCH", f"/api/artifacts/{artifact_id}", {"status": "accepted"})
        self.assertEqual(200, status)
        self.assertEqual("accepted", updated["result"]["artifact"]["status"])
        status, listed = self.request("GET", "/api/artifacts?projectSlug=tower-defense")
        self.assertEqual(200, status)
        self.assertEqual(1, len(listed["result"]["artifacts"]))

    def test_http_report_create_and_fetch(self):
        _, created = self.request(
            "POST",
            "/api/artifacts",
            {
                "kind": "screenshot",
                "path": "shots/two.png",
                "label": "two",
                "projectSlug": "tower-defense",
                "status": "accepted",
            },
        )
        artifact_id = created["result"]["artifact"]["id"]
        status, saved = self.request(
            "POST",
            "/api/reports",
            {
                "projectSlug": "tower-defense",
                "title": "Session",
                "markdown": "![two](shots/two.png)",
                "artifactIds": [artifact_id],
            },
        )
        self.assertEqual(200, status)
        report_id = saved["result"]["report"]["id"]
        status, fetched = self.request("GET", f"/api/reports/{report_id}")
        self.assertEqual(200, status)
        self.assertEqual([artifact_id], fetched["result"]["report"]["artifactIds"])

    def test_http_missing_required_field_returns_bad_request(self):
        status, payload = self.request("POST", "/api/prefs/trigger-mode", {"userId": "will"})
        self.assertEqual(400, status)
        self.assertFalse(payload["ok"])

    def test_http_bootstrap_alias_and_artifacts_alias_work(self):
        self.request("POST", "/api/prefs/active-project", {"userId": "will", "projectSlug": "tower-defense"})
        status, payload = self.request("GET", "/bootstrap?userId=will")
        self.assertEqual(200, status)
        self.assertEqual("tower-defense", payload["result"]["prefs"]["activeProject"])
        self.request(
            "POST",
            "/artifacts",
            {
                "kind": "screenshot",
                "path": "shots/alias.png",
                "label": "alias",
                "projectSlug": "tower-defense",
                "status": "accepted",
            },
        )
        status, payload = self.request("GET", "/artifacts?projectSlug=tower-defense")
        self.assertEqual(200, status)
        self.assertEqual(1, len(payload["result"]["artifacts"]))

    def test_http_artifact_upload_and_static_serve(self):
        status, payload = self.request(
            "POST",
            "/artifacts",
            {
                "image_b64": base64.b64encode(b"pngbytes").decode("ascii"),
                "image_filename": "capture.png",
                "label": "capture",
                "projectSlug": "tower-defense",
            },
        )
        self.assertEqual(200, status)
        path = payload["result"]["artifact"]["path"]
        with urllib.request.urlopen(f"{self.base}{path}", timeout=2) as resp:
            self.assertEqual(200, resp.status)
            self.assertEqual(b"pngbytes", resp.read())

    def test_http_artifact_upload_accepts_camel_case_fields(self):
        status, payload = self.request(
            "POST",
            "/api/artifacts",
            {
                "imageBase64": base64.b64encode(b"camel").decode("ascii"),
                "imageFilename": "capture.png",
                "label": "capture",
                "projectSlug": "tower-defense",
            },
        )
        self.assertEqual(200, status)
        self.assertTrue(payload["result"]["artifact"]["path"].startswith("/uploads/tower-defense/"))

    @patch("backend.http_api.send_chat_turn")
    def test_http_chat_route_delegates_to_chat_bridge(self, mock_chat_turn):
        mock_chat_turn.return_value = {"reply": "hello", "backendTarget": "madeira", "sessionId": "kgu_madeira"}
        status, payload = self.request("POST", "/chat", {"text": "hi", "session": "madeira"})
        self.assertEqual(200, status)
        self.assertEqual("hello", payload["reply"])

    @patch("backend.http_api.load_history")
    def test_http_history_route_returns_messages(self, mock_load_history):
        mock_load_history.return_value = [{"role": "user", "text": "hi", "ts": "04/17 02:00"}]
        status, payload = self.request("GET", "/history/madeira?limit=20")
        self.assertEqual(200, status)
        self.assertEqual(1, payload["total"])

    @patch("backend.http_api.poll_messages")
    def test_http_poll_route_returns_spooled_messages(self, mock_poll_messages):
        mock_poll_messages.return_value = {"messages": [{"role": "agent", "text": "yo"}], "pending_sessions": []}
        status, payload = self.request("GET", "/poll/madeira")
        self.assertEqual(200, status)
        self.assertEqual("yo", payload["messages"][0]["text"])

    @patch("backend.http_api.health")
    def test_http_health_route_returns_runtime_payload(self, mock_health):
        mock_health.return_value = {"status": "ok", "default_session": "madeira"}
        status, payload = self.request("GET", "/health")
        self.assertEqual(200, status)
        self.assertEqual("madeira", payload["default_session"])

    @patch("backend.http_api.list_sessions")
    def test_http_sessions_route_returns_registry_sessions(self, mock_list_sessions):
        mock_list_sessions.return_value = {"sessions": ["madeira", "bella"], "default": "madeira"}
        status, payload = self.request("GET", "/sessions")
        self.assertEqual(200, status)
        self.assertEqual(["madeira", "bella"], payload["sessions"])

    @patch("backend.http_api.agent_status")
    def test_http_agent_status_route_returns_status_payload(self, mock_agent_status):
        mock_agent_status.return_value = {"session": "madeira", "status": "busy", "busy_status": "running"}
        status, payload = self.request("GET", "/agent-status/madeira")
        self.assertEqual(200, status)
        self.assertEqual("busy", payload["status"])

    def test_http_report_create_derives_artifact_ids_and_allows_empty_project(self):
        _, created = self.request(
            "POST",
            "/api/artifacts",
            {
                "kind": "screenshot",
                "path": "/uploads/tower-defense/report-auto.png",
                "label": "report-auto",
                "projectSlug": "tower-defense",
                "status": "accepted",
            },
        )
        artifact_id = created["result"]["artifact"]["id"]
        status, saved = self.request(
            "POST",
            "/api/reports",
            {
                "projectSlug": "",
                "title": "Session",
                "markdown": "![auto](/uploads/tower-defense/report-auto.png)",
                "artifactIds": [],
            },
        )
        self.assertEqual(200, status)
        report = saved["result"]["report"]
        self.assertEqual([artifact_id], report["artifactIds"])
        self.assertIsNone(report["projectSlug"])


if __name__ == "__main__":
    unittest.main()
