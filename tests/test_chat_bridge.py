from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import chat_bridge


class ChatBridgeTests(unittest.TestCase):
    @patch("backend.chat_bridge.harness_send_command")
    def test_send_chat_turn_uses_frontend_turn_contract(self, mock_send):
        mock_send.return_value = {
            "ok": True,
            "result": {"ok": True, "reply_text": "hello", "turn_id": "turn_1"},
        }
        result = chat_bridge.send_chat_turn(text="hi", session="madeira")
        self.assertEqual("hello", result["reply"])
        payload = mock_send.call_args.args[1]
        self.assertEqual("frontend-turn", payload["command"])
        self.assertEqual("madeira", payload["backendTarget"])

    def test_load_history_reads_chatlog_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            date_dir = root / "2026" / "04" / "17" / "frontend_web"
            date_dir.mkdir(parents=True)
            (date_dir / "kgu_madeira.xmlish").write_text(
                '<message direction="in" ts_local="2026-04-17 02:00:00 America/Los_Angeles"><payload>hi</payload></message>\n'
                '<message direction="out" ts_local="2026-04-17 02:01:00 America/Los_Angeles"><payload>hello</payload></message>\n',
                encoding="utf-8",
            )
            with patch.object(chat_bridge, "CHATLOG_ROOT", root):
                messages = chat_bridge.load_history("kgu-madeira", limit=10)
        self.assertEqual(["user", "agent"], [m["role"] for m in messages])

    def test_poll_messages_consumes_spool_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_dir = root / "madeira"
            session_dir.mkdir(parents=True)
            (session_dir / "msg1.json").write_text(
                json.dumps({"text": "follow-up", "sender": "madeira"}),
                encoding="utf-8",
            )
            with patch.object(chat_bridge, "FRONTEND_PUSH_ROOT", root):
                payload = chat_bridge.poll_messages("madeira")
                remaining = list(session_dir.glob("*.json"))
        self.assertEqual("follow-up", payload["messages"][0]["text"])
        self.assertEqual([], remaining)
