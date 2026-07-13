from __future__ import annotations

import csv
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_CATEGORIES = {
    "Documents": [".doc", ".docx", ".md", ".pdf", ".rtf", ".txt"],
    "Spreadsheets": [".csv", ".ods", ".xls", ".xlsx"],
    "Images": [".bmp", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".svg", ".webp"],
    "Video": [".avi", ".m4v", ".mov", ".mp4", ".webm"],
    "Audio": [".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"],
    "Archives": [".7z", ".gz", ".rar", ".tar", ".zip"],
    "Code": [".css", ".html", ".java", ".js", ".json", ".py", ".sh", ".sql", ".ts", ".yaml", ".yml"],
}


@dataclass(frozen=True)
class FileAction:
    source: str
    destination: str
    category: str
    extension: str
    size_bytes: int
    sha256: str
    status: str
    collision: bool = False


@dataclass(frozen=True)
class OrganisationPlan:
    created_at: str
    source_root: str
    destination_root: str
    mode: str
    recursive: bool
    actions: list[FileAction]

    @property
    def total_bytes(self) -> int:
        return sum(action.size_bytes for action in self.actions)

    @property
    def categories(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for action in self.actions:
            totals[action.category] = totals.get(action.category, 0) + 1
        return dict(sorted(totals.items()))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_categories(config_path: Path | None = None) -> dict[str, list[str]]:
    if config_path is None:
        return DEFAULT_CATEGORIES
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    categories = payload.get("categories", payload)
    if not isinstance(categories, dict) or not categories:
        raise ValueError("Configuration must contain a non-empty 'categories' object")
    return {str(name): [str(ext).lower() if str(ext).startswith(".") else f".{str(ext).lower()}" for ext in extensions]
            for name, extensions in categories.items()}


def classify(path: Path, categories: dict[str, list[str]]) -> str:
    extension = path.suffix.lower()
    return next((name for name, extensions in categories.items() if extension in extensions), "Other")


def unique_destination(path: Path, reserved: set[Path]) -> tuple[Path, bool]:
    if path not in reserved and not path.exists():
        reserved.add(path)
        return path, False
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if candidate not in reserved and not candidate.exists():
            reserved.add(candidate)
            return candidate, True
        counter += 1


def build_plan(source: Path, destination: Path, *, mode: str = "copy", recursive: bool = False,
               categories: dict[str, list[str]] | None = None) -> OrganisationPlan:
    source, destination = source.resolve(), destination.resolve()
    if not source.is_dir():
        raise ValueError(f"Source folder does not exist: {source}")
    if source == destination or source in destination.parents:
        raise ValueError("Destination cannot be the source or a parent of the source")
    if destination in source.parents:
        raise ValueError("Destination cannot contain the source folder")
    if mode not in {"copy", "move"}:
        raise ValueError("Mode must be 'copy' or 'move'")

    categories = categories or DEFAULT_CATEGORIES
    iterator = source.rglob("*") if recursive else source.iterdir()
    files = [item for item in iterator if item.is_file() and not item.name.startswith(".")]
    reserved: set[Path] = set()
    actions = []
    for item in sorted(files, key=lambda value: str(value).lower()):
        category = classify(item, categories)
        relative_parent = item.parent.relative_to(source) if recursive and item.parent != source else Path()
        proposed = destination / category / relative_parent / item.name
        final, collision = unique_destination(proposed, reserved)
        actions.append(FileAction(str(item), str(final), category, item.suffix.lower() or "(none)",
                                  item.stat().st_size, file_hash(item), "planned", collision))
    return OrganisationPlan(datetime.now(timezone.utc).isoformat(timespec="seconds"), str(source), str(destination), mode, recursive, actions)


def execute_plan(plan: OrganisationPlan) -> OrganisationPlan:
    completed = []
    for action in plan.actions:
        source, destination = Path(action.source), Path(action.destination)
        if not source.exists():
            completed.append(FileAction(**{**asdict(action), "status": "source_missing"}))
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if plan.mode == "copy":
            shutil.copy2(source, destination)
        else:
            shutil.move(str(source), str(destination))
        completed.append(FileAction(**{**asdict(action), "status": "completed"}))
    return OrganisationPlan(plan.created_at, plan.source_root, plan.destination_root, plan.mode, plan.recursive, completed)


def undo_manifest(manifest_path: Path) -> dict[str, int]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload["mode"] != "move":
        raise ValueError("Undo is only available for move operations")
    restored = skipped = 0
    for action in reversed(payload["actions"]):
        source, destination = Path(action["source"]), Path(action["destination"])
        if action["status"] != "completed" or not destination.exists() or source.exists():
            skipped += 1
            continue
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(destination), str(source))
        restored += 1
    return {"restored": restored, "skipped": skipped}


def write_manifest(plan: OrganisationPlan, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**asdict(plan), "summary": {"files": len(plan.actions), "bytes": plan.total_bytes, "categories": plan.categories}}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_csv_report(plan: OrganisationPlan, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(plan.actions[0]).keys()) if plan.actions else ["source", "destination", "status"])
        writer.writeheader()
        writer.writerows(asdict(action) for action in plan.actions)
    return path
