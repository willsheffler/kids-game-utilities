from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import runtime_bridge


class RuntimeBridgeTests(unittest.TestCase):
    def test_health_returns_basic_identity(self):
        payload = runtime_bridge.health()
        self.assertEqual("ok", payload["status"])
        self.assertIn("default_session", payload)

    def test_list_sessions_reads_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "agent_registry.json"
            registry.write_text(
                json.dumps({"agents": [{"session": "madeira"}, {"session": "bella"}]}),
                encoding="utf-8",
            )
            with patch.object(runtime_bridge, "REGISTRY_PATH", registry):
                payload = runtime_bridge.list_sessions()
        self.assertEqual(["bella", "madeira"], payload["sessions"])

    @patch("backend.runtime_bridge._send_harness_command")
    def test_agent_status_maps_harness_payload(self, mock_send):
        mock_send.return_value = {
            "ok": True,
            "result": {
                "pane_command": "codex",
                "status": "busy",
                "busy_status": "running",
                "last_line": "working",
                "runtime_family": "codex_cli",
                "logical_actor": "madeira",
            },
        }
        payload = runtime_bridge.agent_status("madeira")
        self.assertEqual("busy", payload["status"])
        self.assertEqual("codex", payload["pane_command"])
