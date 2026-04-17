from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.store import KidsGameStore


class KidsGameStoreTests(unittest.TestCase):
    def make_store(self) -> tuple[tempfile.TemporaryDirectory[str], KidsGameStore]:
        tmp = tempfile.TemporaryDirectory()
        return tmp, KidsGameStore(tmp.name)

    def test_prefs_persist_active_project_across_restart(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        store.set_active_project("will", "tower-defense")
        reloaded = KidsGameStore(tmp.name)
        self.assertEqual("tower-defense", reloaded.get_active_project("will")["active_project"])

    def test_prefs_persist_trigger_mode_across_restart(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        store.set_trigger_mode("will", "mention")
        reloaded = KidsGameStore(tmp.name)
        self.assertEqual("mention", reloaded.get_trigger_mode("will")["trigger_mode"])

    def test_artifact_create_suggested_then_accept_updates_manifest(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_artifact(
            kind="screenshot",
            path="session-logs/assets/a.png",
            label="boss fight",
            project_slug="tower-defense",
        )
        updated = store.update_artifact(artifact["id"], status="accepted", label="boss fight clear")
        self.assertEqual("accepted", updated["status"])
        self.assertEqual("boss fight clear", updated["label"])
        reloaded = KidsGameStore(tmp.name)
        saved = reloaded.get_artifact(artifact["id"])
        self.assertEqual("accepted", saved["status"])

    def test_artifact_dismiss_preserves_manifest_entry(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_artifact(
            kind="screenshot",
            path="session-logs/assets/b.png",
            label="menu",
            project_slug="tower-defense",
        )
        store.update_artifact(artifact["id"], status="dismissed")
        listed = store.list_artifacts(project_slug="tower-defense", status="dismissed")
        self.assertEqual([artifact["id"]], [item["id"] for item in listed])

    def test_artifact_soft_delete_hides_from_default_listing_but_preserves_record(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_artifact(
            kind="screenshot",
            path="session-logs/assets/c.png",
            label="paused",
            project_slug="tower-defense",
        )
        store.update_artifact(artifact["id"], status="deleted")
        self.assertEqual([], store.list_artifacts(project_slug="tower-defense"))
        self.assertEqual([artifact["id"]], [item["id"] for item in store.list_artifacts(project_slug="tower-defense", include_deleted=True)])

    def test_artifact_list_filters_by_project_slug(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        td = store.create_artifact(kind="screenshot", path="a.png", label="td", project_slug="tower-defense")
        pl = store.create_artifact(kind="screenshot", path="b.png", label="pl", project_slug="platformer")
        self.assertEqual([td["id"]], [item["id"] for item in store.list_artifacts(project_slug="tower-defense")])
        self.assertEqual([pl["id"]], [item["id"] for item in store.list_artifacts(project_slug="platformer")])

    def test_report_create_persists_markdown_and_artifact_ids(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_artifact(
            kind="screenshot",
            path="session-logs/assets/d.png",
            label="win",
            project_slug="tower-defense",
            status="accepted",
        )
        report = store.create_or_update_report(
            project_slug="tower-defense",
            title="Session 1",
            markdown="![win](session-logs/assets/d.png)",
            artifact_ids=[artifact["id"]],
        )
        reloaded = KidsGameStore(tmp.name)
        saved = reloaded.get_report(report["id"])
        self.assertEqual("Session 1", saved["title"])
        self.assertEqual([artifact["id"]], saved["artifact_ids"])

    def test_report_and_manifest_linkage_remain_consistent(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        first = store.create_artifact(kind="screenshot", path="one.png", label="one", project_slug="tower-defense", status="accepted")
        second = store.create_artifact(kind="screenshot", path="two.png", label="two", project_slug="tower-defense", status="accepted")
        report = store.create_or_update_report(
            project_slug="tower-defense",
            title="Session 1",
            markdown="![one](one.png)",
            artifact_ids=[first["id"]],
        )
        store.create_or_update_report(
            report_id=report["id"],
            project_slug="tower-defense",
            title="Session 1",
            markdown="![two](two.png)",
            artifact_ids=[second["id"]],
        )
        first_saved = store.get_artifact(first["id"])
        second_saved = store.get_artifact(second["id"])
        self.assertEqual([], first_saved["linked_report_ids"])
        self.assertEqual([report["id"]], second_saved["linked_report_ids"])

    def test_report_update_preserves_existing_linkage_when_expected(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_artifact(kind="screenshot", path="x.png", label="x", project_slug="tower-defense", status="accepted")
        report = store.create_or_update_report(
            project_slug="tower-defense",
            title="Session",
            markdown="draft",
            artifact_ids=[artifact["id"]],
        )
        updated = store.create_or_update_report(
            report_id=report["id"],
            project_slug="tower-defense",
            title="Session revised",
            markdown="draft 2",
            artifact_ids=[artifact["id"]],
        )
        self.assertEqual([artifact["id"]], updated["artifact_ids"])
        self.assertEqual([report["id"]], store.get_artifact(artifact["id"])["linked_report_ids"])

    def test_markdown_image_paths_render_from_persisted_artifact_paths(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_artifact(
            kind="screenshot",
            path="session-logs/assets/2026-04-17/win.png",
            label="win",
            project_slug="tower-defense",
            status="accepted",
        )
        report = store.create_or_update_report(
            project_slug="tower-defense",
            title="Session",
            markdown=f"![win]({artifact['path']})",
            artifact_ids=[artifact["id"]],
        )
        self.assertIn(artifact["path"], report["markdown"])

    def test_uploaded_artifact_writes_file_and_manifest_record(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_uploaded_artifact(
            filename="boss.png",
            content_bytes=b"pngdata",
            label="boss wave",
            project_slug="tower-defense",
            mime_type="image/png",
        )
        self.assertTrue(artifact["path"].startswith("/uploads/tower-defense/"))
        saved = Path(tmp.name) / ".kids-game-utilities" / artifact["path"].lstrip("/")
        self.assertTrue(saved.exists())
        self.assertEqual(b"pngdata", saved.read_bytes())

    def test_report_derives_artifact_ids_from_markdown_paths(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_artifact(
            kind="screenshot",
            path="/uploads/tower-defense/jump.png",
            label="jump",
            project_slug="tower-defense",
            status="accepted",
        )
        report = store.create_or_update_report(
            project_slug="tower-defense",
            title="Session",
            markdown="![jump](/uploads/tower-defense/jump.png)",
            artifact_ids=[],
        )
        self.assertEqual([artifact["id"]], report["artifact_ids"])
        self.assertEqual([report["id"]], store.get_artifact(artifact["id"])["linked_report_ids"])

    def test_repeated_report_save_does_not_duplicate_artifact_linkage(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        artifact = store.create_artifact(
            kind="screenshot",
            path="/uploads/tower-defense/repeat.png",
            label="repeat",
            project_slug="tower-defense",
            status="accepted",
        )
        report = store.create_or_update_report(
            project_slug="tower-defense",
            title="Session",
            markdown="![repeat](/uploads/tower-defense/repeat.png)",
            artifact_ids=[],
        )
        updated = store.create_or_update_report(
            report_id=report["id"],
            project_slug="tower-defense",
            title="Session",
            markdown="![repeat](/uploads/tower-defense/repeat.png)",
            artifact_ids=[],
        )
        self.assertEqual([artifact["id"]], updated["artifact_ids"])
        self.assertEqual([report["id"]], store.get_artifact(artifact["id"])["linked_report_ids"])

    def test_report_allows_unscoped_project_slug(self):
        tmp, store = self.make_store()
        self.addCleanup(tmp.cleanup)
        report = store.create_or_update_report(
            project_slug=None,
            title="Session",
            markdown="text",
            artifact_ids=[],
        )
        self.assertIsNone(report["project_slug"])


if __name__ == "__main__":
    unittest.main()
