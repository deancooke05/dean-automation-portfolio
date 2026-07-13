from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from threading import Lock

from .engine import (
    OrganisationPlan,
    build_plan,
    execute_plan,
    load_categories,
    undo_manifest,
    write_csv_report,
    write_manifest,
)
from .report import build_html_report, format_size


class OrganiserService:
    """Stateful application service shared by the web interface and tests."""

    def __init__(self, base: Path):
        self.base = base.resolve()
        self.output = self.base / "outputs"
        self.output.mkdir(parents=True, exist_ok=True)
        self._plan: OrganisationPlan | None = None
        self._lock = Lock()

    @property
    def default_source(self) -> Path:
        return self.base / "sample_messy_folder"

    @property
    def default_destination(self) -> Path:
        return self.output / "organised_files"

    def defaults(self) -> dict:
        return {
            "source": "sample_messy_folder",
            "destination": "outputs/organised_files",
            "mode": "copy",
            "recursive": False,
        }

    def preview(
        self,
        source: str,
        destination: str,
        *,
        mode: str = "copy",
        recursive: bool = False,
        config: str | None = None,
    ) -> dict:
        categories = load_categories(self._path(config)) if config else None
        plan = build_plan(
            self._path(source),
            self._path(destination),
            mode=mode,
            recursive=recursive,
            categories=categories,
        )
        with self._lock:
            self._plan = plan
            self._write_outputs(plan, completed=False)
        return self.serialise(plan)

    def _path(self, value: str) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else self.base / path

    def apply(self) -> dict:
        with self._lock:
            if self._plan is None:
                raise ValueError("Create a preview before organising files")
            completed = execute_plan(self._plan)
            self._plan = completed
            self._write_outputs(completed, completed=True)
        payload = self.serialise(completed)
        payload["report_url"] = "/report"
        payload["manifest"] = str(self.output / "completed_manifest.json")
        return payload

    def undo(self) -> dict:
        manifest = self.output / "completed_manifest.json"
        if not manifest.exists():
            raise ValueError("No completed move operation is available to undo")
        result = undo_manifest(manifest)
        self._plan = None
        return result

    def _write_outputs(self, plan: OrganisationPlan, *, completed: bool) -> None:
        manifest_name = "completed_manifest.json" if completed else "preview_manifest.json"
        write_manifest(plan, self.output / manifest_name)
        write_csv_report(plan, self.output / "audit_report.csv")
        build_html_report(plan, self.output / "organisation_report.html")

    @staticmethod
    def serialise(plan: OrganisationPlan) -> dict:
        completed = sum(action.status == "completed" for action in plan.actions)
        return {
            "created_at": plan.created_at,
            "source_root": plan.source_root,
            "destination_root": plan.destination_root,
            "mode": plan.mode,
            "recursive": plan.recursive,
            "summary": {
                "files": len(plan.actions),
                "categories": len(plan.categories),
                "category_counts": plan.categories,
                "bytes": plan.total_bytes,
                "formatted_size": format_size(plan.total_bytes),
                "collisions": sum(action.collision for action in plan.actions),
                "completed": completed,
            },
            "actions": [
                {
                    **asdict(action),
                    "file_name": Path(action.source).name,
                    "destination_display": str(Path(action.destination).relative_to(plan.destination_root)),
                    "formatted_size": format_size(action.size_bytes),
                }
                for action in plan.actions
            ],
        }
