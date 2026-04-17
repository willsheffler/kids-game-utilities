from __future__ import annotations

import base64
import tempfile
import unittest

from backend.api import KidsGameAPI


class KidsGameAPITests(unittest.TestCase):
    def make_api(self) -> tuple[tempfile.TemporaryDirectory[str], KidsGameAPI]:
        tmp = tempfile.TemporaryDirectory()
        return tmp, KidsGameAPI(tmp.name)

    def test_bootstrap_returns_prefs_and_known_projects(self):
        tmp, api = self.make_api()
        self.addCleanup(tmp.cleanup)
        api.set_active_project(user_id="will", project_slug="tower-defense")
        api.set_trigger_mode(user_id="will", mode="mention")
        api.create_artifact(
            kind="screenshot",
            path="shots/one.png",
            label="one",
            project_slug="tower-defense",
            status="accepted",
        )

        payload = api.get_bootstrap(user_id="will")
        self.assertTrue(payload["ok"])
        self.assertEqual("tower-defense", payload["result"]["prefs"]["activeProject"])
        self.assertEqual("mention", payload["result"]["prefs"]["triggerMode"])
        self.assertEqual(
            [{"slug": "tower-defense", "label": "tower-defense"}],
            payload["result"]["projects"],
        )

    def test_trigger_mode_payload_uses_canonical_names(self):
        tmp, api = self.make_api()
        self.addCleanup(tmp.cleanup)
        payload = api.set_trigger_mode(user_id="will", mode="manual")
        self.assertEqual("manual", payload["result"]["triggerMode"])

    def test_artifact_payload_uses_frontend_facing_keys(self):
        tmp, api = self.make_api()
        self.addCleanup(tmp.cleanup)
        payload = api.create_artifact(
            kind="screenshot",
            path="shots/two.png",
            label="two",
            project_slug="tower-defense",
            status="suggested",
            mime_type="image/png",
        )
        artifact = payload["result"]["artifact"]
        self.assertEqual("tower-defense", artifact["projectSlug"])
        self.assertEqual("image/png", artifact["mimeType"])
        self.assertIn("linkedReportIds", artifact)
        self.assertEqual("two.png", artifact["filename"])
        self.assertEqual("shots/two.png", artifact["url"])

    def test_list_artifacts_filters_and_returns_payloads(self):
        tmp, api = self.make_api()
        self.addCleanup(tmp.cleanup)
        api.create_artifact(kind="screenshot", path="a.png", label="a", project_slug="tower-defense", status="accepted")
        api.create_artifact(kind="screenshot", path="b.png", label="b", project_slug="platformer", status="dismissed")
        payload = api.list_artifacts(project_slug="tower-defense")
        self.assertEqual(1, len(payload["result"]["artifacts"]))
        self.assertEqual("tower-defense", payload["result"]["artifacts"][0]["projectSlug"])

    def test_report_payload_uses_explicit_artifact_ids(self):
        tmp, api = self.make_api()
        self.addCleanup(tmp.cleanup)
        artifact = api.create_artifact(
            kind="screenshot",
            path="shots/three.png",
            label="three",
            project_slug="tower-defense",
            status="accepted",
        )["result"]["artifact"]
        payload = api.create_or_update_report(
            project_slug="tower-defense",
            title="Session",
            markdown="![three](shots/three.png)",
            artifact_ids=[artifact["id"]],
        )
        report = payload["result"]["report"]
        self.assertEqual([artifact["id"]], report["artifactIds"])
        self.assertEqual("tower-defense", report["projectSlug"])

    def test_list_projects_combines_report_and_artifact_projects(self):
        tmp, api = self.make_api()
        self.addCleanup(tmp.cleanup)
        artifact = api.create_artifact(
            kind="screenshot",
            path="shots/four.png",
            label="four",
            project_slug="tower-defense",
            status="accepted",
        )["result"]["artifact"]
        api.create_or_update_report(
            project_slug="platformer",
            title="Session",
            markdown="text",
            artifact_ids=[],
        )
        payload = api.list_projects()
        self.assertEqual(
            [
                {"slug": "platformer", "label": "platformer"},
                {"slug": "tower-defense", "label": "tower-defense"},
            ],
            payload["result"]["projects"],
        )

    def test_upload_artifact_returns_served_upload_path(self):
        tmp, api = self.make_api()
        self.addCleanup(tmp.cleanup)
        payload = api.upload_artifact(
            image_b64=base64.b64encode(b"img").decode("ascii"),
            image_filename="capture.png",
            label="capture",
            project_slug="tower-defense",
        )
        artifact = payload["result"]["artifact"]
        self.assertTrue(artifact["path"].startswith("/uploads/tower-defense/"))
        self.assertEqual("accepted", artifact["status"])

    def test_report_payload_derives_artifact_ids_from_markdown_when_omitted(self):
        tmp, api = self.make_api()
        self.addCleanup(tmp.cleanup)
        artifact = api.create_artifact(
            kind="screenshot",
            path="/uploads/tower-defense/report.png",
            label="report",
            project_slug="tower-defense",
            status="accepted",
        )["result"]["artifact"]
        payload = api.create_or_update_report(
            project_slug="tower-defense",
            title="Session",
            markdown="![report](/uploads/tower-defense/report.png)",
            artifact_ids=[],
        )
        self.assertEqual([artifact["id"]], payload["result"]["report"]["artifactIds"])


if __name__ == "__main__":
    unittest.main()
