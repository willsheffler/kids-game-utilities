from __future__ import annotations

import json
import shutil
import tempfile
import uuid
from base64 import b64decode
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class KidsGameStore:
    """File-backed v1 persistence for prefs, artifacts, and reports."""

    DEFAULT_TRIGGER_MODE = "auto"
    VALID_TRIGGER_MODES = {"auto", "mention", "manual"}
    VALID_ARTIFACT_STATUSES = {"suggested", "accepted", "dismissed", "deleted"}

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.state_dir = self.root / ".kids-game-utilities"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir = self.state_dir / "uploads"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self._prefs_path = self.state_dir / "prefs.json"
        self._artifact_manifest_path = self.state_dir / "artifacts.json"
        self._reports_path = self.state_dir / "reports.json"
        self._ensure_file(self._prefs_path, {"users": {}})
        self._ensure_file(self._artifact_manifest_path, {"version": 1, "artifacts": []})
        self._ensure_file(self._reports_path, {"reports": []})

    def _ensure_file(self, path: Path, default_payload: dict[str, Any]) -> None:
        if not path.exists():
            self._write_json(path, default_payload)

    def _read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def _safe_filename(self, filename: str) -> str:
        raw = Path(filename or "artifact.bin").name
        cleaned = "".join(ch for ch in raw if ch.isalnum() or ch in {".", "_", "-"})
        return cleaned or "artifact.bin"

    def save_upload(
        self,
        *,
        filename: str,
        content_bytes: bytes,
        project_slug: str | None,
    ) -> str:
        project_dir = self.uploads_dir / (project_slug or "_unscoped")
        project_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix or ".bin"
        stem = Path(filename).stem or "artifact"
        safe_name = f"{self._safe_filename(stem)}_{uuid.uuid4().hex[:8]}{suffix}"
        dest = project_dir / safe_name
        with tempfile.NamedTemporaryFile(dir=project_dir, delete=False) as tmp:
            tmp.write(content_bytes)
            tmp_path = Path(tmp.name)
        tmp_path.replace(dest)
        relative = dest.relative_to(self.state_dir)
        return f"/{relative.as_posix()}"

    def create_uploaded_artifact(
        self,
        *,
        filename: str,
        content_bytes: bytes,
        label: str,
        project_slug: str | None,
        status: str = "accepted",
        description: str | None = None,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        path = self.save_upload(filename=filename, content_bytes=content_bytes, project_slug=project_slug)
        kind = "screenshot" if (mime_type or "").startswith("image/") or path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")) else "file"
        return self.create_artifact(
            kind=kind,
            path=path,
            label=label,
            project_slug=project_slug,
            status=status,
            description=description,
            mime_type=mime_type,
        )

    # prefs
    def get_active_project(self, user_id: str) -> dict[str, Any]:
        prefs = self._read_json(self._prefs_path)
        user = prefs["users"].get(user_id, {})
        return {"user_id": user_id, "active_project": user.get("active_project")}

    def set_active_project(self, user_id: str, project_slug: str | None) -> dict[str, Any]:
        prefs = self._read_json(self._prefs_path)
        user = prefs["users"].setdefault(user_id, {})
        user["active_project"] = project_slug
        user["updated_at"] = _now_iso()
        self._write_json(self._prefs_path, prefs)
        return {"user_id": user_id, "active_project": project_slug}

    def get_trigger_mode(self, user_id: str) -> dict[str, Any]:
        prefs = self._read_json(self._prefs_path)
        user = prefs["users"].get(user_id, {})
        return {"user_id": user_id, "trigger_mode": user.get("trigger_mode", self.DEFAULT_TRIGGER_MODE)}

    def set_trigger_mode(self, user_id: str, mode: str) -> dict[str, Any]:
        mode = str(mode).strip().lower()
        if mode not in self.VALID_TRIGGER_MODES:
            raise ValueError(f"invalid trigger mode: {mode}")
        prefs = self._read_json(self._prefs_path)
        user = prefs["users"].setdefault(user_id, {})
        user["trigger_mode"] = mode
        user["updated_at"] = _now_iso()
        self._write_json(self._prefs_path, prefs)
        return {"user_id": user_id, "trigger_mode": mode}

    # artifacts
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
        if status not in self.VALID_ARTIFACT_STATUSES:
            raise ValueError(f"invalid artifact status: {status}")
        manifest = self._read_json(self._artifact_manifest_path)
        now = _now_iso()
        artifact = {
            "id": self._new_id("artifact"),
            "project_slug": project_slug,
            "kind": kind,
            "status": status,
            "label": label,
            "description": description,
            "path": path,
            "mime_type": mime_type,
            "created_at": now,
            "updated_at": now,
            "linked_report_ids": [],
        }
        manifest["artifacts"].append(artifact)
        self._write_json(self._artifact_manifest_path, manifest)
        return artifact

    def update_artifact(self, artifact_id: str, **changes: Any) -> dict[str, Any]:
        manifest = self._read_json(self._artifact_manifest_path)
        artifact = self._find_artifact(manifest, artifact_id)
        if "status" in changes:
            status = str(changes["status"]).strip().lower()
            if status not in self.VALID_ARTIFACT_STATUSES:
                raise ValueError(f"invalid artifact status: {status}")
            artifact["status"] = status
        for field in ("label", "description", "project_slug", "path", "mime_type"):
            if field in changes:
                artifact[field] = changes[field]
        if "linked_report_ids" in changes:
            artifact["linked_report_ids"] = sorted(set(changes["linked_report_ids"] or []))
        artifact["updated_at"] = _now_iso()
        self._write_json(self._artifact_manifest_path, manifest)
        return artifact

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        manifest = self._read_json(self._artifact_manifest_path)
        return dict(self._find_artifact(manifest, artifact_id))

    def list_artifacts(
        self,
        *,
        project_slug: str | None = None,
        include_deleted: bool = False,
        status: str | None = None,
        linked_report_id: str | None = None,
    ) -> list[dict[str, Any]]:
        manifest = self._read_json(self._artifact_manifest_path)
        artifacts = [dict(item) for item in manifest["artifacts"]]
        if project_slug is not None:
            artifacts = [item for item in artifacts if item.get("project_slug") == project_slug]
        if not include_deleted:
            artifacts = [item for item in artifacts if item.get("status") != "deleted"]
        if status is not None:
            artifacts = [item for item in artifacts if item.get("status") == status]
        if linked_report_id is not None:
            artifacts = [item for item in artifacts if linked_report_id in item.get("linked_report_ids", [])]
        artifacts.sort(key=lambda item: item["created_at"])
        return artifacts

    def _find_artifact(self, manifest: dict[str, Any], artifact_id: str) -> dict[str, Any]:
        for artifact in manifest["artifacts"]:
            if artifact["id"] == artifact_id:
                return artifact
        raise KeyError(f"unknown artifact: {artifact_id}")

    # reports
    def create_or_update_report(
        self,
        *,
        report_id: str | None = None,
        project_slug: str | None,
        title: str,
        markdown: str,
        artifact_ids: list[str],
    ) -> dict[str, Any]:
        reports_payload = self._read_json(self._reports_path)
        manifest = self._read_json(self._artifact_manifest_path)
        derived_artifact_ids = self._artifact_ids_from_markdown(markdown, manifest)
        artifact_ids = sorted(set(list(artifact_ids or []) + derived_artifact_ids))
        for artifact_id in artifact_ids:
            self._find_artifact(manifest, artifact_id)
        now = _now_iso()
        report = None
        if report_id is not None:
            for candidate in reports_payload["reports"]:
                if candidate["id"] == report_id:
                    report = candidate
                    break
        if report is None:
            report = {
                "id": report_id or self._new_id("report"),
                "created_at": now,
            }
            reports_payload["reports"].append(report)
        report.update(
            {
                "project_slug": project_slug,
                "title": title,
                "markdown": markdown,
                "artifact_ids": artifact_ids,
                "updated_at": now,
            }
        )

        report_id = report["id"]
        for artifact in manifest["artifacts"]:
            linked = set(artifact.get("linked_report_ids", []))
            if artifact["id"] in artifact_ids:
                linked.add(report_id)
            else:
                linked.discard(report_id)
            artifact["linked_report_ids"] = sorted(linked)
            artifact["updated_at"] = now if artifact["id"] in artifact_ids or report_id in linked else artifact["updated_at"]
        self._write_json(self._reports_path, reports_payload)
        self._write_json(self._artifact_manifest_path, manifest)
        return dict(report)

    def _artifact_ids_from_markdown(self, markdown: str, manifest: dict[str, Any]) -> list[str]:
        if not markdown:
            return []
        matches = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', markdown)
        if not matches:
            return []
        derived_ids: list[str] = []
        for match in matches:
            path = match.strip()
            for artifact in manifest["artifacts"]:
                if artifact.get("path") == path and artifact["id"] not in derived_ids:
                    derived_ids.append(artifact["id"])
        return derived_ids

    def get_report(self, report_id: str) -> dict[str, Any]:
        reports_payload = self._read_json(self._reports_path)
        for report in reports_payload["reports"]:
            if report["id"] == report_id:
                return dict(report)
        raise KeyError(f"unknown report: {report_id}")

    def list_reports(self, *, project_slug: str | None = None) -> list[dict[str, Any]]:
        reports_payload = self._read_json(self._reports_path)
        reports = [dict(item) for item in reports_payload["reports"]]
        if project_slug is not None:
            reports = [item for item in reports if item.get("project_slug") == project_slug]
        reports.sort(key=lambda item: item["created_at"])
        return reports
