from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from src.engine import build_plan, execute_plan, load_categories, undo_manifest, write_csv_report, write_manifest
from src.report import build_html_report


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description="Preview, apply or undo a safe file-organisation plan.")
    cli.add_argument("source", nargs="?", default=str(BASE / "sample_messy_folder"))
    cli.add_argument("--destination", default=str(BASE / "outputs" / "organised_files"))
    cli.add_argument("--mode", choices=["copy", "move"], default="copy")
    cli.add_argument("--recursive", action="store_true")
    cli.add_argument("--apply", action="store_true", help="Execute the plan. Preview is the safe default.")
    cli.add_argument("--config", type=Path)
    cli.add_argument("--undo", type=Path, help="Undo a completed move manifest.")
    cli.add_argument("--clean-demo-output", action="store_true")
    return cli


def main() -> None:
    args = parser().parse_args()
    output = BASE / "outputs"
    if args.clean_demo_output and output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    if args.undo:
        result = undo_manifest(args.undo)
        print(f"Restored {result['restored']} file(s); skipped {result['skipped']}.")
        return
    plan = build_plan(Path(args.source), Path(args.destination), mode=args.mode, recursive=args.recursive,
                      categories=load_categories(args.config))
    if args.apply:
        plan = execute_plan(plan)
    manifest = write_manifest(plan, output / ("completed_manifest.json" if args.apply else "preview_manifest.json"))
    write_csv_report(plan, output / "audit_report.csv")
    report = build_html_report(plan, output / "organisation_report.html")
    print(f"{'Applied' if args.apply else 'Previewed'} {len(plan.actions)} file(s) across {len(plan.categories)} categories.")
    print(f"Manifest: {manifest}")
    print(f"Report:   {report}")


if __name__ == "__main__":
    main()
