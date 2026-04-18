"""
Property-based tests for KidsGameStore using hypothesis.

These complement the example-based tests in test_store.py by testing
invariants that must hold for arbitrary inputs.

Usage:
    python -m pytest tests/test_store_properties.py -v
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, note
from hypothesis import strategies as st

from backend.store import KidsGameStore

# ── Strategies ──────────────────────────────────────────────────────────

# Safe text that won't break JSON or filesystem paths
safe_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"), blacklist_characters="\x00/\\"),
    min_size=1,
    max_size=60,
)

user_ids = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), blacklist_characters="\x00"),
    min_size=1,
    max_size=30,
)

project_slugs = st.from_regex(r"[a-z][a-z0-9\-]{0,29}", fullmatch=True)
trigger_modes = st.sampled_from(["auto", "mention", "manual"])
artifact_statuses = st.sampled_from(["suggested", "accepted", "dismissed", "deleted"])
artifact_kinds = st.sampled_from(["screenshot", "file", "code", "asset"])
file_paths = st.from_regex(r"assets/[a-z0-9_]{1,20}\.(png|jpg|js|css|html)", fullmatch=True)


@pytest.fixture
def store():
    tmp = tempfile.TemporaryDirectory()
    s = KidsGameStore(tmp.name)
    yield s
    tmp.cleanup()


# ── Prefs properties ───────────────────────────────────────────────────

class TestPrefsProperties:

    @given(user_id=user_ids, project=project_slugs)
    @settings(max_examples=50)
    def test_active_project_round_trips(self, user_id, project):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            store.set_active_project(user_id, project)
            result = store.get_active_project(user_id)
            assert result["active_project"] == project
            assert result["user_id"] == user_id

    @given(user_id=user_ids, mode=trigger_modes)
    @settings(max_examples=50)
    def test_trigger_mode_round_trips(self, user_id, mode):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            store.set_trigger_mode(user_id, mode)
            result = store.get_trigger_mode(user_id)
            assert result["trigger_mode"] == mode

    @given(user_id=user_ids, mode=st.text(min_size=1, max_size=20))
    @settings(max_examples=50)
    def test_invalid_trigger_mode_raises(self, user_id, mode):
        assume(mode.strip().lower() not in {"auto", "mention", "manual"})
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            with pytest.raises(ValueError):
                store.set_trigger_mode(user_id, mode)

    @given(
        users=st.lists(
            st.tuples(user_ids, project_slugs, trigger_modes),
            min_size=2,
            max_size=5,
            unique_by=lambda t: t[0],
        )
    )
    @settings(max_examples=30)
    def test_prefs_are_isolated_per_user(self, users):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            for uid, proj, mode in users:
                store.set_active_project(uid, proj)
                store.set_trigger_mode(uid, mode)
            for uid, proj, mode in users:
                assert store.get_active_project(uid)["active_project"] == proj
                assert store.get_trigger_mode(uid)["trigger_mode"] == mode

    @given(user_id=user_ids, mode=trigger_modes)
    @settings(max_examples=30)
    def test_trigger_mode_survives_reload(self, user_id, mode):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            store.set_trigger_mode(user_id, mode)
            reloaded = KidsGameStore(tmp)
            assert reloaded.get_trigger_mode(user_id)["trigger_mode"] == mode


# ── Artifact properties ────────────────────────────────────────────────

class TestArtifactProperties:

    @given(
        kind=artifact_kinds,
        path=file_paths,
        label=safe_text,
        project=project_slugs,
        status=artifact_statuses,
    )
    @settings(max_examples=50)
    def test_create_preserves_all_fields(self, kind, path, label, project, status):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            art = store.create_artifact(
                kind=kind, path=path, label=label,
                project_slug=project, status=status,
            )
            assert art["kind"] == kind
            assert art["path"] == path
            assert art["label"] == label
            assert art["project_slug"] == project
            assert art["status"] == status
            assert art["id"].startswith("artifact_")
            assert art["linked_report_ids"] == []

    @given(
        kind=artifact_kinds,
        path=file_paths,
        label=safe_text,
        project=project_slugs,
    )
    @settings(max_examples=30)
    def test_create_then_get_round_trips(self, kind, path, label, project):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            created = store.create_artifact(
                kind=kind, path=path, label=label, project_slug=project,
            )
            fetched = store.get_artifact(created["id"])
            for key in ("id", "kind", "path", "label", "project_slug", "status"):
                assert fetched[key] == created[key]

    @given(status=st.text(min_size=1, max_size=20))
    @settings(max_examples=30)
    def test_invalid_status_raises(self, status):
        assume(status not in {"suggested", "accepted", "dismissed", "deleted"})
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            with pytest.raises(ValueError):
                store.create_artifact(
                    kind="file", path="x.png", label="x",
                    project_slug="test", status=status,
                )

    @given(
        items=st.lists(
            st.tuples(artifact_kinds, file_paths, safe_text, project_slugs),
            min_size=1,
            max_size=8,
            unique_by=lambda t: t[1],  # unique paths
        )
    )
    @settings(max_examples=30)
    def test_list_filters_correctly_by_project(self, items):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            created = {}
            for kind, path, label, project in items:
                art = store.create_artifact(
                    kind=kind, path=path, label=label, project_slug=project,
                )
                created[art["id"]] = project
            # Every project filter should return only its own artifacts
            for project in set(created.values()):
                listed = store.list_artifacts(project_slug=project)
                for art in listed:
                    assert art["project_slug"] == project

    @given(
        kind=artifact_kinds,
        path=file_paths,
        label=safe_text,
        project=project_slugs,
    )
    @settings(max_examples=30)
    def test_soft_delete_hides_from_default_list(self, kind, path, label, project):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            art = store.create_artifact(
                kind=kind, path=path, label=label, project_slug=project,
            )
            store.update_artifact(art["id"], status="deleted")
            default = store.list_artifacts(project_slug=project)
            with_deleted = store.list_artifacts(project_slug=project, include_deleted=True)
            assert art["id"] not in [a["id"] for a in default]
            assert art["id"] in [a["id"] for a in with_deleted]


# ── Report properties ──────────────────────────────────────────────────

class TestReportProperties:

    @given(
        project=project_slugs,
        title=safe_text,
        markdown=safe_text,
    )
    @settings(max_examples=30)
    def test_create_report_round_trips(self, project, title, markdown):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            report = store.create_or_update_report(
                project_slug=project, title=title,
                markdown=markdown, artifact_ids=[],
            )
            fetched = store.get_report(report["id"])
            assert fetched["title"] == title
            assert fetched["markdown"] == markdown
            assert fetched["project_slug"] == project

    @given(
        project=project_slugs,
        title=safe_text,
    )
    @settings(max_examples=30)
    def test_report_derives_artifact_links_from_markdown(self, project, title):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            art = store.create_artifact(
                kind="screenshot", path="/uploads/test/img.png",
                label="test", project_slug=project,
            )
            report = store.create_or_update_report(
                project_slug=project, title=title,
                markdown="![test](/uploads/test/img.png)",
                artifact_ids=[],
            )
            assert art["id"] in report["artifact_ids"]
            linked = store.get_artifact(art["id"])
            assert report["id"] in linked["linked_report_ids"]

    @given(
        projects=st.lists(project_slugs, min_size=2, max_size=4, unique=True),
        title=safe_text,
    )
    @settings(max_examples=20)
    def test_reports_filter_by_project(self, projects, title):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            ids_by_project = {}
            for proj in projects:
                r = store.create_or_update_report(
                    project_slug=proj, title=f"{title}-{proj}",
                    markdown="text", artifact_ids=[],
                )
                ids_by_project[proj] = r["id"]
            for proj in projects:
                listed = store.list_reports(project_slug=proj)
                listed_ids = {r["id"] for r in listed}
                assert ids_by_project[proj] in listed_ids
                for other_proj, other_id in ids_by_project.items():
                    if other_proj != proj:
                        assert other_id not in listed_ids

    @given(project=st.none() | project_slugs, title=safe_text)
    @settings(max_examples=20)
    def test_report_accepts_null_project(self, project, title):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            report = store.create_or_update_report(
                project_slug=project, title=title,
                markdown="text", artifact_ids=[],
            )
            assert report["project_slug"] == project


# ── Upload properties ──────────────────────────────────────────────────

class TestUploadProperties:

    @given(
        label=safe_text,
        project=project_slugs,
        content=st.binary(min_size=1, max_size=100),
    )
    @settings(max_examples=20)
    def test_upload_creates_serveable_file(self, label, project, content):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            art = store.create_uploaded_artifact(
                filename="test.png", content_bytes=content,
                label=label, project_slug=project,
                mime_type="image/png",
            )
            assert art["path"].startswith("/uploads/")
            file_path = Path(tmp) / ".kids-game-utilities" / art["path"].lstrip("/")
            assert file_path.exists()
            assert file_path.read_bytes() == content

    @given(
        filename=st.from_regex(r"[a-z]{1,10}\.(png|jpg|gif)", fullmatch=True),
        project=project_slugs,
    )
    @settings(max_examples=20)
    def test_upload_path_contains_project(self, filename, project):
        with tempfile.TemporaryDirectory() as tmp:
            store = KidsGameStore(tmp)
            art = store.create_uploaded_artifact(
                filename=filename, content_bytes=b"x",
                label="test", project_slug=project,
            )
            assert f"/uploads/{project}/" in art["path"]
