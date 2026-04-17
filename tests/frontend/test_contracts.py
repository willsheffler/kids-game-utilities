"""
Contract tests: verify backend API response shapes match frontend expectations.

Run these before integration to catch field-name drift between frontend and backend.
Both Loom (frontend) and Rivet (backend) should run these.

Usage:
    python -m pytest tests/frontend/test_contracts.py -v
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
import urllib.request
import urllib.error

BACKEND_URL = "http://localhost:8790"
TEST_USER = "will"


def _get(path):
    resp = urllib.request.urlopen(f"{BACKEND_URL}{path}")
    return json.loads(resp.read())


def _post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def _patch(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


@pytest.fixture(scope="session", autouse=True)
def check_backend():
    """Verify backend is running before tests."""
    try:
        urllib.request.urlopen(f"{BACKEND_URL}/api/projects", timeout=2)
    except Exception:
        pytest.skip(f"Backend not running at {BACKEND_URL}")


class TestBootstrapContract:
    def test_returns_ok_and_result(self):
        data = _get(f"/api/bootstrap?userId={TEST_USER}")
        assert data["ok"] is True
        assert "result" in data

    def test_result_has_prefs(self):
        data = _get(f"/api/bootstrap?userId={TEST_USER}")
        prefs = data["result"]["prefs"]
        assert "activeProject" in prefs
        assert "triggerMode" in prefs

    def test_result_has_projects(self):
        data = _get(f"/api/bootstrap?userId={TEST_USER}")
        assert "projects" in data["result"]
        assert isinstance(data["result"]["projects"], list)

    def test_trigger_mode_is_valid(self):
        data = _get(f"/api/bootstrap?userId={TEST_USER}")
        assert data["result"]["prefs"]["triggerMode"] in ("auto", "mention", "manual")


class TestArtifactsContract:
    def test_list_returns_array(self):
        data = _get("/api/artifacts")
        assert data["ok"] is True
        assert isinstance(data["result"]["artifacts"], list)

    def test_create_with_path_returns_artifact_shape(self):
        data = _post("/api/artifacts", {
            "kind": "screenshot",
            "label": "test contract screenshot (path)",
            "path": "session-logs/assets/test/contract_test.png",
            "projectSlug": "test-project",
        })
        assert data["ok"] is True
        art = data["result"]["artifact"]
        for field in ("id", "kind", "status", "label", "path", "createdAt", "updatedAt", "linkedReportIds"):
            assert field in art, f"Missing field: {field}"
        assert art["kind"] == "screenshot"
        assert art["status"] in ("suggested", "accepted", "dismissed", "deleted")

    def test_create_with_image_upload_returns_artifact_shape(self):
        """Test the image upload path used by the screenshot capture UI."""
        import base64
        # Minimal 1x1 PNG
        tiny_png = base64.b64encode(bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
            0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00,
            0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
            0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC, 0x33, 0x00, 0x00, 0x00,
            0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
        ])).decode()
        data = _post("/api/artifacts", {
            "kind": "screenshot",
            "label": "test upload screenshot",
            "image_b64": tiny_png,
            "image_filename": "test_upload.png",
            "projectSlug": "test-project",
        })
        assert data["ok"] is True
        art = data["result"]["artifact"]
        assert art["path"].startswith("/uploads/") or "session-logs" in art["path"]
        assert art["label"] == "test upload screenshot"

    def test_list_filters_by_project(self):
        data = _get("/api/artifacts?projectSlug=nonexistent-project")
        assert data["ok"] is True
        # Should return empty or only matching artifacts
        assert isinstance(data["result"]["artifacts"], list)


class TestPrefsContract:
    def test_get_trigger_mode(self):
        data = _get(f"/api/prefs/trigger-mode?userId={TEST_USER}")
        assert data["ok"] is True
        assert "triggerMode" in data["result"]

    def test_set_trigger_mode(self):
        data = _post("/api/prefs/trigger-mode", {
            "userId": TEST_USER,
            "mode": "mention",
        })
        assert data["ok"] is True
        # Verify it persisted
        data2 = _get(f"/api/prefs/trigger-mode?userId={TEST_USER}")
        assert data2["result"]["triggerMode"] == "mention"
        # Reset
        _post("/api/prefs/trigger-mode", {"userId": TEST_USER, "mode": "auto"})

    def test_set_active_project(self):
        data = _post("/api/prefs/active-project", {
            "userId": TEST_USER,
            "projectSlug": "test-project",
        })
        assert data["ok"] is True


class TestReportsContract:
    def test_list_returns_array(self):
        data = _get("/api/reports")
        assert data["ok"] is True
        assert isinstance(data["result"]["reports"], list)

    def test_create_report_returns_shape(self):
        data = _post("/api/reports", {
            "projectSlug": "test-project",
            "title": "Test Report",
            "markdown": "# Test\n\nThis is a test report.",
            "artifactIds": [],
        })
        assert data["ok"] is True
        report = data["result"]["report"]
        for field in ("id", "title", "markdown", "artifactIds", "createdAt", "updatedAt"):
            assert field in report, f"Missing field: {field}"


class TestProjectsContract:
    def test_list_returns_array(self):
        data = _get("/api/projects")
        assert data["ok"] is True
        assert isinstance(data["result"]["projects"], list)

    def test_project_shape(self):
        # Create some data first so projects are derived
        _post("/api/artifacts", {"kind": "screenshot", "label": "for project list", "path": "session-logs/assets/test/proj.png", "projectSlug": "contract-test-proj"})
        data = _get("/api/projects")
        projects = data["result"]["projects"]
        if projects:
            p = projects[0]
            assert "slug" in p
            assert "label" in p
