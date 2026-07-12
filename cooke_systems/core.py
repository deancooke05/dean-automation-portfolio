from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: str | Path, rows: list[dict], fields: list[str] | None = None) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return destination


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip()
    return re.sub(r"[ -]+", "_", value) or "untitled"


def organise_files(source: str | Path, destination: str | Path, apply: bool = False) -> list[dict]:
    source, destination = Path(source), Path(destination)
    plan = []
    for item in sorted(source.iterdir()):
        if not item.is_file() or item.name.startswith("."):
            continue
        category = item.suffix.lower().lstrip(".") or "no_extension"
        target = destination / category / item.name
        plan.append({"source": str(item), "destination": str(target), "category": category})
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(target))
    return plan


def rename_invoices(folder: str | Path, mapping_csv: str | Path, apply: bool = False) -> list[dict]:
    folder = Path(folder)
    plan = []
    for row in read_csv(mapping_csv):
        source = folder / row["current_name"]
        new = f"{row['date']}_{safe_name(row['supplier'])}_{safe_name(row['invoice_number'])}{source.suffix.lower()}"
        target = folder / new
        plan.append({"source": str(source), "destination": str(target), "exists": source.exists()})
        if apply and source.exists():
            source.rename(target)
    return plan


def create_backup(source: str | Path, output: str | Path) -> Path:
    source, output = Path(source), Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = []
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(source.rglob("*")):
            if item.is_file():
                relative = item.relative_to(source)
                archive.write(item, relative)
                manifest.append({"path": str(relative), "sha256": sha256(item), "bytes": item.stat().st_size})
        archive.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, indent=2))
    return output


def analyse_prices(path: str | Path) -> dict:
    rows = read_csv(path)
    grouped: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in rows:
        grouped[row["product"]].append((row["date"], float(row["price"])))
    products = []
    for name, values in grouped.items():
        values.sort()
        first, latest = values[0][1], values[-1][1]
        products.append({"product": name, "first_price": first, "latest_price": latest,
                         "change_percent": round((latest - first) / first * 100, 2),
                         "lowest_price": min(v for _, v in values)})
    return {"products": products, "observations": len(rows)}


def score_tenders(path: str | Path, keywords: list[str], min_value: float = 0) -> list[dict]:
    results = []
    keywords = [k.lower() for k in keywords]
    for row in read_csv(path):
        text = f"{row.get('title','')} {row.get('description','')}".lower()
        matches = [keyword for keyword in keywords if keyword in text]
        value = float(row.get("value", 0) or 0)
        score = len(matches) * 20 + (20 if value >= min_value else 0)
        results.append({**row, "matched_keywords": ", ".join(matches), "score": min(score, 100)})
    return sorted(results, key=lambda row: int(row["score"]), reverse=True)


def find_duplicates(folder: str | Path) -> list[dict]:
    groups: dict[tuple[int, str], list[str]] = defaultdict(list)
    for item in Path(folder).rglob("*"):
        if item.is_file():
            groups[(item.stat().st_size, sha256(item))].append(str(item))
    return [{"bytes": key[0], "sha256": key[1], "files": files} for key, files in groups.items() if len(files) > 1]


def merge_text_documents(inputs: list[str | Path], output: str | Path) -> Path:
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sections = []
    for source in inputs:
        source = Path(source)
        sections.append(f"\n{'=' * 72}\n{source.name}\n{'=' * 72}\n{source.read_text(encoding='utf-8')}")
    destination.write_text("\n".join(sections).lstrip(), encoding="utf-8")
    return destination


def image_manifest(folder: str | Path) -> list[dict]:
    extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tiff", ".bmp"}
    rows = []
    for index, item in enumerate(sorted(Path(folder).iterdir()), 1):
        if item.is_file() and item.suffix.lower() in extensions:
            rows.append({"current_name": item.name, "suggested_name": f"image_{index:03d}{item.suffix.lower()}",
                         "bytes": item.stat().st_size, "sha256": sha256(item)})
    return rows


def analyse_log(path: str | Path) -> dict:
    severities = Counter()
    messages = Counter()
    pattern = re.compile(r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL)\b[: ]*(.*)", re.I)
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        match = pattern.search(line)
        if match:
            severity = match.group(1).upper().replace("WARN", "WARNING")
            severities[severity] += 1
            messages[match.group(2).strip()] += 1
    return {"lines": len(lines), "severities": dict(severities), "top_messages": messages.most_common(10)}


def audit_csv(path: str | Path) -> dict:
    rows = read_csv(path)
    fields = list(rows[0]) if rows else []
    missing = {field: sum(not str(row.get(field, "")).strip() for row in rows) for field in fields}
    duplicates = len(rows) - len({tuple(row.get(field, "") for field in fields) for row in rows})
    return {"rows": len(rows), "columns": len(fields), "fields": fields, "missing": missing, "duplicate_rows": duplicates}


def build_quote(path: str | Path, tax_rate: float = 0.2) -> dict:
    rows = read_csv(path)
    items, subtotal = [], 0.0
    for row in rows:
        quantity, unit_price = float(row["quantity"]), float(row["unit_price"])
        total = quantity * unit_price
        subtotal += total
        items.append({**row, "line_total": round(total, 2)})
    tax = subtotal * tax_rate
    return {"items": items, "subtotal": round(subtotal, 2), "tax": round(tax, 2), "total": round(subtotal + tax, 2)}


def expense_summary(path: str | Path, rules: dict[str, list[str]]) -> dict:
    totals = defaultdict(float)
    categorized = []
    for row in read_csv(path):
        description = row["description"].lower()
        category = next((name for name, words in rules.items() if any(word.lower() in description for word in words)), "Other")
        amount = float(row["amount"])
        totals[category] += amount
        categorized.append({**row, "category": category})
    return {"totals": {key: round(value, 2) for key, value in totals.items()}, "transactions": categorized}


def reorder_plan(path: str | Path) -> list[dict]:
    results = []
    for row in read_csv(path):
        stock = float(row["stock"]); daily = float(row["daily_demand"]); lead = float(row["lead_days"]); safety = float(row["safety_stock"])
        point = daily * lead + safety
        order = max(0.0, point - stock)
        results.append({**row, "reorder_point": round(point, 2), "recommended_order": round(order, 2), "status": "REORDER" if order else "OK"})
    return results


def find_schedule_conflicts(path: str | Path) -> list[dict]:
    rows = read_csv(path)
    parsed = [(row, datetime.fromisoformat(row["start"]), datetime.fromisoformat(row["end"])) for row in rows]
    conflicts = []
    for index, (left, left_start, left_end) in enumerate(parsed):
        for right, right_start, right_end in parsed[index + 1:]:
            if left_start < right_end and right_start < left_end:
                conflicts.append({"event_a": left["event"], "event_b": right["event"],
                                  "overlap_start": max(left_start, right_start).isoformat(timespec="minutes"),
                                  "overlap_end": min(left_end, right_end).isoformat(timespec="minutes")})
    return conflicts


def folder_snapshot(folder: str | Path) -> dict[str, dict]:
    root = Path(folder)
    return {str(item.relative_to(root)): {"bytes": item.stat().st_size, "sha256": sha256(item)}
            for item in root.rglob("*") if item.is_file()}


def compare_snapshots(before: dict, after: dict) -> dict:
    before_keys, after_keys = set(before), set(after)
    return {"added": sorted(after_keys - before_keys), "removed": sorted(before_keys - after_keys),
            "changed": sorted(key for key in before_keys & after_keys if before[key] != after[key])}


def package_handover(folder: str | Path, output: str | Path, required: list[str] | None = None) -> dict:
    folder = Path(folder); required = required or ["README.md"]
    missing = [name for name in required if not (folder / name).exists()]
    if missing:
        raise ValueError("Missing required handover files: " + ", ".join(missing))
    create_backup(folder, output)
    return {"archive": str(output), "files": len(folder_snapshot(folder)), "sha256": sha256(output)}


def sla_dashboard(path: str | Path) -> dict:
    rows = read_csv(path)
    durations = [float(row["resolution_hours"]) for row in rows]
    met = sum(row.get("sla_met", "").lower() in {"yes", "true", "1"} for row in rows)
    return {"tickets": len(rows), "sla_met_percent": round(met / len(rows) * 100, 1) if rows else 0,
            "average_resolution_hours": round(statistics.mean(durations), 2) if durations else 0,
            "median_resolution_hours": round(statistics.median(durations), 2) if durations else 0}


def lead_ranker(path: str | Path) -> list[dict]:
    results = []
    for row in read_csv(path):
        score = int(float(row.get("budget", 0)) >= 1000) * 30 + int(row.get("urgency", "").lower() == "high") * 30
        score += int(row.get("fit", "").lower() in {"strong", "excellent"}) * 40
        results.append({**row, "score": score, "priority": "High" if score >= 70 else "Medium" if score >= 40 else "Low"})
    return sorted(results, key=lambda item: item["score"], reverse=True)
