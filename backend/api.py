from __future__ import annotations

from pathlib import Path
from typing import Any
from base64 import b64decode

from .store import KidsGameStore


class KidsGameAPI:
    """Thin frontend-facing adapter over the file-backed store."""

    def __init__(self, root: str | Path):
        self.store = KidsGameStore(root)

    def get_bootstrap(self, *, user_id: str) -> dict[str, Any]:
        active_project = self.store.get_active_project(user_id)["active_project"]
        trigger_mode = self.store.get_trigger_mode(user_id)["trigger_mode"]
        projects = self.list_projects()["result"]["projects"]
        return {
            "ok": True,
            "result": {
                "prefs": {
                    "activeProject": active_project,
                    "triggerMode": trigger_mode,
                },
                "projects": projects,
            },
        }

    def get_active_project(self, *, user_id: str) -> dict[str, Any]:
        result = self.store.get_active_project(user_id)
        return {"ok": True, "result": {"userId": user_id, "activeProject": result["active_project"]}}

    def set_active_project(self, *, user_id: str, project_slug: str | None) -> dict[str, Any]:
        result = self.store.set_active_project(user_id, project_slug)
        return {"ok": True, "result": {"userId": user_id, "activeProject": result["active_project"]}}

    def get_trigger_mode(self, *, user_id: str) -> dict[str, Any]:
        result = self.store.get_trigger_mode(user_id)
        return {"ok": True, "result": {"userId": user_id, "triggerMode": result["trigger_mode"]}}

    def set_trigger_mode(self, *, user_id: str, mode: str) -> dict[str, Any]:
        result = self.store.set_trigger_mode(user_id, mode)
        return {"ok": True, "result": {"userId": user_id, "triggerMode": result["trigger_mode"]}}

    def list_projects(self) -> dict[str, Any]:
        project_slugs = set()
        for artifact in self.store.list_artifacts(include_deleted=True):
            if artifact.get("project_slug"):
                project_slugs.add(artifact["project_slug"])
        for report in self.store.list_reports():
            if report.get("project_slug"):
                project_slugs.add(report["project_slug"])
        projects = [{"slug": slug, "label": slug} for slug in sorted(project_slugs)]
        return {"ok": True, "result": {"projects": projects}}

    def create_artifact(
        self,
        *,
        kind: str,
        path: str,
        label: str,
        project_slug: str | None,
        status: str = "suggested",
        description: str | None = None,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        artifact = self.store.create_artifact(
            kind=kind,
            path=path,
            label=label,
            project_slug=project_slug,
            status=status,
            description=description,
            mime_type=mime_type,
        )
        return {"ok": True, "result": {"artifact": self._artifact_payload(artifact)}}

    def upload_artifact(
        self,
        *,
        image_b64: str,
        image_filename: str,
        label: str,
        project_slug: str | None,
        mime_type: str | None = "image/png",
        description: str | None = None,
        status: str = "accepted",
    ) -> dict[str, Any]:
        content = b64decode(image_b64)
        artifact = self.store.create_uploaded_artifact(
            filename=image_filename,
            content_bytes=content,
            label=label,
            project_slug=project_slug,
            status=status,
            description=description,
            mime_type=mime_type,
        )
        return {"ok": True, "result": {"artifact": self._artifact_payload(artifact)}}

    def update_artifact(self, artifact_id: str, **changes: Any) -> dict[str, Any]:
        artifact = self.store.update_artifact(artifact_id, **changes)
        return {"ok": True, "result": {"artifact": self._artifact_payload(artifact)}}

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        artifact = self.store.get_artifact(artifact_id)
        return {"ok": True, "result": {"artifact": self._artifact_payload(artifact)}}

    def list_artifacts(
        self,
        *,
        project_slug: str | None = None,
        include_deleted: bool = False,
        status: str | None = None,
        linked_report_id: str | None = None,
    ) -> dict[str, Any]:
        artifacts = self.store.list_artifacts(
            project_slug=project_slug,
            include_deleted=include_deleted,
            status=status,
            linked_report_id=linked_report_id,
        )
        return {"ok": True, "result": {"artifacts": [self._artifact_payload(item) for item in artifacts]}}

    def create_or_update_report(
        self,
        *,
        report_id: str | None = None,
        project_slug: str | None,
        title: str,
        markdown: str,
        artifact_ids: list[str],
    ) -> dict[str, Any]:
        report = self.store.create_or_update_report(
            report_id=report_id,
            project_slug=project_slug,
            title=title,
            markdown=markdown,
            artifact_ids=artifact_ids,
        )
        return {"ok": True, "result": {"report": self._report_payload(report)}}

    def get_report(self, report_id: str) -> dict[str, Any]:
        report = self.store.get_report(report_id)
        return {"ok": True, "result": {"report": self._report_payload(report)}}

    def list_reports(self, *, project_slug: str | None = None) -> dict[str, Any]:
        reports = self.store.list_reports(project_slug=project_slug)
        return {"ok": True, "result": {"reports": [self._report_payload(item) for item in reports]}}

    def _artifact_payload(self, artifact: dict[str, Any]) -> dict[str, Any]:
        path = artifact["path"]
        return {
            "id": artifact["id"],
            "kind": artifact["kind"],
            "projectSlug": artifact.get("project_slug"),
            "status": artifact["status"],
            "label": artifact["label"],
            "description": artifact.get("description"),
            "path": path,
            "url": path,
            "filename": Path(path).name,
            "mimeType": artifact.get("mime_type"),
            "createdAt": artifact["created_at"],
            "updatedAt": artifact["updated_at"],
            "linkedReportIds": list(artifact.get("linked_report_ids", [])),
        }

    def _report_payload(self, report: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": report["id"],
            "projectSlug": report["project_slug"],
            "title": report["title"],
            "markdown": report["markdown"],
            "artifactIds": list(report["artifact_ids"]),
            "createdAt": report["created_at"],
            "updatedAt": report["updated_at"],
        }
