"""Generate the consistent product shells, examples and documentation for Products 003–020."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent

PRODUCTS = {
3:("Smart File Organiser","Plans and applies safe file organisation by file type.","organise"),
4:("Invoice Renamer","Applies consistent, searchable invoice filenames from a mapping file.","invoice"),
5:("Versioned Backup Tool","Creates verified ZIP backups with a SHA-256 manifest.","backup"),
6:("Price Tracker Analyser","Turns offline price history into clear price-change intelligence.","prices"),
7:("Tender Opportunity Scorer","Ranks public tender exports against practical business criteria.","tenders"),
8:("Duplicate File Finder","Finds duplicate files by content rather than unreliable filenames.","duplicates"),
9:("Document Pack Builder","Combines text documents into a structured, auditable pack.","documents"),
10:("Image Library Auditor","Creates a renaming and integrity manifest for image libraries.","images"),
11:("Log Insight Analyser","Summarises severity and repeated messages from application logs.","logs"),
12:("Data Quality Auditor","Reports missing data, duplicate rows and structural CSV issues.","quality"),
13:("Quote Builder","Calculates itemised quotes, tax and totals from a simple CSV export.","quote"),
14:("Expense Categoriser","Applies transparent keyword rules to business expenses.","expenses"),
15:("Inventory Reorder Planner","Calculates reorder points and recommended purchase quantities.","inventory"),
16:("Schedule Conflict Checker","Finds overlapping appointments before they become problems.","schedule"),
17:("Folder Change Monitor","Creates and compares cryptographic folder snapshots.","monitor"),
18:("Client Handover Packager","Validates and packages delivery folders with checksums.","handover"),
19:("Service SLA Dashboard","Summarises ticket resolution performance and SLA compliance.","sla"),
20:("Client Lead Ranker","Ranks enquiries by commercial fit, urgency and budget.","leads"),
}

FOLDERS = {
    3: "03_file_organiser",
    4: "04_invoice_renamer",
    5: "05_folder_backup_tool",
    6: "06_price_tracker_demo",
    7: "07_tenderscout_case_study",
}

RUNNER = '''from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cooke_systems import core

PRODUCT = {product!r}
BASE = Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description={description!r})
    parser.add_argument("input", nargs="?", default=str(BASE/"sample_data"/"input.csv"))
    parser.add_argument("--output", default=str(BASE/"outputs"/"result.json"))
    parser.add_argument("--apply", action="store_true", help="Apply file changes for products that support execution; preview is the default.")
    args=parser.parse_args(); source=Path(args.input); output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists() and (BASE/"sample_data"/"input").exists(): source=BASE/"sample_data"/"input"
    if PRODUCT=="organise": result=core.organise_files(source, output.parent/"organised", args.apply)
    elif PRODUCT=="invoice": result=core.rename_invoices(source.parent/"files", source, args.apply)
    elif PRODUCT=="backup": result={{"archive":str(core.create_backup(source, output.with_suffix(".zip")))}}
    elif PRODUCT=="prices": result=core.analyse_prices(source)
    elif PRODUCT=="tenders": result=core.score_tenders(source,["automation","engineering","software"],1000)
    elif PRODUCT=="duplicates": result=core.find_duplicates(source)
    elif PRODUCT=="documents": result={{"output":str(core.merge_text_documents(sorted(source.glob("*.txt")),output.with_suffix(".txt")))}}
    elif PRODUCT=="images": result=core.image_manifest(source)
    elif PRODUCT=="logs": result=core.analyse_log(source)
    elif PRODUCT=="quality": result=core.audit_csv(source)
    elif PRODUCT=="quote": result=core.build_quote(source)
    elif PRODUCT=="expenses": result=core.expense_summary(source,{{"Software":["github","adobe","microsoft"],"Travel":["rail","uber","fuel"],"Office":["stationery","paper"]}})
    elif PRODUCT=="inventory": result=core.reorder_plan(source)
    elif PRODUCT=="schedule": result=core.find_schedule_conflicts(source)
    elif PRODUCT=="monitor": result=core.folder_snapshot(source)
    elif PRODUCT=="handover": result=core.package_handover(source,output.with_suffix(".zip"))
    elif PRODUCT=="sla": result=core.sla_dashboard(source)
    elif PRODUCT=="leads": result=core.lead_ranker(source)
    else: raise ValueError(PRODUCT)
    if not (isinstance(result,dict) and "archive" in result and len(result)==1): output.write_text(json.dumps(result,indent=2,default=str),encoding="utf-8")
    print(json.dumps(result,indent=2,default=str))

if __name__=="__main__": main()
'''

README = '''# Product {number:03d} — {name}

![Cooke Automation Systems](../brand/logo.svg)

{description}

## Why it exists

This product removes a repetitive administrative step while keeping the workflow transparent and reviewable. It runs locally and does not transmit customer data.

## Run the demonstration

From the portfolio root:

```bash
python3 {folder}/run.py
```

Results are written to the product's `outputs` folder. File-changing products use preview mode unless `--apply` is explicitly supplied.

## Product standard

- Local-first and privacy-conscious
- Clear input and output contracts
- Safe defaults
- Reusable Python implementation
- Automated portfolio test coverage
- Shared Cooke Automation Systems visual identity

Version 1.0.0
'''

SAMPLES = {
"prices":"date,product,price\n2026-06-01,Telemetry Unit,499\n2026-07-01,Telemetry Unit,449\n2026-06-01,Control Board,250\n2026-07-01,Control Board,265\n",
"tenders":"title,description,value\nAutomation support,Python automation for reporting,5000\nOffice cleaning,Weekly facilities contract,12000\nEngineering dashboard,Software dashboard for engineering team,9000\n",
"quality":"id,name,email\n1,Ada,ada@example.com\n2,,bob@example.com\n2,,bob@example.com\n",
"quote":"description,quantity,unit_price\nAutomation setup,1,450\nData migration,3,85\nDocumentation,2,45\n",
"expenses":"date,description,amount\n2026-07-01,GitHub subscription,15\n2026-07-02,National Rail,42.50\n2026-07-03,Stationery supplies,18.20\n",
"inventory":"sku,stock,daily_demand,lead_days,safety_stock\nCAL-01,12,4,5,5\nCAL-02,80,3,7,10\n",
"schedule":"event,start,end\nClient call,2026-07-12T10:00,2026-07-12T11:00\nProject review,2026-07-12T10:30,2026-07-12T11:30\nStudy block,2026-07-12T13:00,2026-07-12T15:00\n",
"sla":"ticket,resolution_hours,sla_met\nT-001,2.5,yes\nT-002,9,no\nT-003,4,yes\n",
"leads":"client,budget,urgency,fit\nAero North,2500,high,strong\nLocal Shop,400,low,medium\nMaker Works,1200,medium,excellent\n",
"invoice":"current_name,date,supplier,invoice_number\ninvoice1.pdf,2026-07-01,Example Supplies,INV-1001\n",
}

def build():
    for number,(name,description,product) in PRODUCTS.items():
        folder=FOLDERS.get(number, f"{number:02d}_"+name.lower().replace(" ","_").replace("-",""))
        target=ROOT/folder; (target/"sample_data").mkdir(parents=True,exist_ok=True); (target/"outputs").mkdir(exist_ok=True)
        (target/"run.py").write_text(RUNNER.format(product=product,description=description),encoding="utf-8")
        (target/"README.md").write_text(README.format(number=number,name=name,description=description,folder=folder),encoding="utf-8")
        (target/"CHANGELOG.md").write_text(f"# Changelog\n\n## 1.0.0 — 12 July 2026\n\n- Initial verified portfolio release of {name}.\n",encoding="utf-8")
        sample=SAMPLES.get(product,"name,value\nExample,1\n")
        if product in {"organise","duplicates","documents","images","monitor","handover","backup"}:
            sample_dir=target/"sample_data"/"input"; sample_dir.mkdir(exist_ok=True)
            (sample_dir/"README.md").write_text("Sample file used to demonstrate the local workflow.\n",encoding="utf-8")
            if product=="documents": (sample_dir/"brief.txt").write_text("Project brief\n",encoding="utf-8")
        elif product=="logs":
            (target/"sample_data"/"input.csv").write_text("2026-07-12 INFO Started\n2026-07-12 ERROR Connection failed\n2026-07-12 WARNING Retrying\n",encoding="utf-8")
        else: (target/"sample_data"/"input.csv").write_text(sample,encoding="utf-8")
        if product=="invoice":
            files=target/"sample_data"/"files"; files.mkdir(exist_ok=True); (files/"invoice1.pdf").write_bytes(b"%PDF-1.4 sample")
    print(json.dumps({"products_created":len(PRODUCTS)},indent=2))

if __name__=="__main__": build()
