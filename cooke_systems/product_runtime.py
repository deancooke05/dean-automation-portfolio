from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Callable

from . import core


PRODUCTS = {
    "001": ("Messy CSV Cleaner", "Turn unreliable customer data into a clean, dependable dataset.", "DATA REFINEMENT", "sample_data/messy_customers.csv"),
    "002": ("Excel Report Generator", "Transform raw sales exports into an executive-ready workbook.", "EXECUTIVE REPORTING", "sample_data/sample_sales.csv"),
    "004": ("Invoice Renamer", "Give every invoice a consistent, searchable and audit-friendly name.", "FINANCE OPERATIONS", "sample_data/input.csv"),
    "005": ("Versioned Backup Tool", "Create a verified archive with a cryptographic record of every file.", "BUSINESS CONTINUITY", "sample_data/input"),
    "006": ("Price Tracker Analyser", "See price movement, buying opportunities and unusual changes instantly.", "COMMERCIAL INTELLIGENCE", "sample_data/input.csv"),
    "007": ("Tender Opportunity Scorer", "Rank opportunities by strategic fit, value and relevant capability.", "OPPORTUNITY INTELLIGENCE", "sample_data/input.csv"),
    "008": ("Duplicate File Finder", "Find wasted storage using content evidence—not unreliable filenames.", "STORAGE INTELLIGENCE", "sample_data/input"),
    "009": ("Document Pack Builder", "Turn scattered notes into one structured and traceable review pack.", "DOCUMENT OPERATIONS", "sample_data/input"),
    "010": ("Image Library Auditor", "Catalogue image assets, verify integrity and plan consistent names.", "ASSET GOVERNANCE", "sample_data/input"),
    "011": ("Log Insight Analyser", "Convert noisy application logs into a focused operational briefing.", "RELIABILITY INTELLIGENCE", "sample_data/input.csv"),
    "012": ("Data Quality Auditor", "Measure missing data, duplicates and structural weaknesses before they spread.", "DATA ASSURANCE", "sample_data/input.csv"),
    "013": ("Quote Builder", "Produce clear, accurate pricing with itemised totals and tax.", "COMMERCIAL OPERATIONS", "sample_data/input.csv"),
    "014": ("Expense Categoriser", "Turn raw transactions into a transparent spending view.", "FINANCE INTELLIGENCE", "sample_data/input.csv"),
    "015": ("Inventory Reorder Planner", "Convert stock levels and demand into confident purchasing decisions.", "SUPPLY OPERATIONS", "sample_data/input.csv"),
    "016": ("Schedule Conflict Checker", "Find overlapping commitments before they become customer problems.", "PLANNING ASSURANCE", "sample_data/input.csv"),
    "017": ("Folder Change Monitor", "Create a cryptographic baseline and reveal exactly what changed.", "CHANGE ASSURANCE", "sample_data/input"),
    "018": ("Client Handover Packager", "Validate, seal and verify a professional delivery archive.", "DELIVERY ASSURANCE", "sample_data/input"),
    "019": ("Service SLA Dashboard", "Expose service performance, response risk and compliance at a glance.", "SERVICE INTELLIGENCE", "sample_data/input.csv"),
    "020": ("Client Lead Ranker", "Focus attention on enquiries with the strongest commercial potential.", "SALES INTELLIGENCE", "sample_data/input.csv"),
}


def spec(product_id: str) -> dict:
    name, promise, category, default = PRODUCTS[product_id]
    return {"id": product_id, "name": name, "promise": promise, "category": category, "default_input": default}


def metric(label: str, value, note: str) -> dict:
    return {"label": label, "value": str(value), "note": note}


def insight(title: str, body: str, tone: str = "neutral") -> dict:
    return {"title": title, "body": body, "tone": tone}


def human_size(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def money(value: float) -> str:
    return f"£{value:,.2f}"


def analyse(product_id: str, base: Path, source_value: str, options: dict | None = None) -> dict:
    options = options or {}
    source = Path(source_value).expanduser()
    if not source.is_absolute():
        source = base / source
    if not source.exists():
        raise ValueError(f"Input does not exist: {source}")
    handlers: dict[str, Callable] = {
        "001": _csv_cleaner, "002": _excel_report, "004": _invoice_renamer,
        "005": _backup, "006": _prices, "007": _tenders, "008": _duplicates,
        "009": _documents, "010": _images, "011": _logs, "012": _quality,
        "013": _quote, "014": _expenses, "015": _inventory, "016": _schedule,
        "017": _monitor, "018": _handover, "019": _sla, "020": _leads,
    }
    result = handlers[product_id](base, source, options)
    result.update({"product_id": product_id, "product_name": PRODUCTS[product_id][0], "source": display_path(base, source)})
    return _write_artifacts(base, result)


def apply_preview(product_id: str, base: Path, result: dict) -> dict:
    if product_id != "004":
        raise ValueError("This product has no separate apply step")
    applied = []
    for row in result.get("rows", []):
        source, destination = Path(row["source"]), Path(row["destination"])
        source = source if source.is_absolute() else base / source
        destination = destination if destination.is_absolute() else base / destination
        if row.get("status") != "Ready" or not source.exists():
            applied.append({**row, "status": "Skipped"})
            continue
        if destination.exists():
            applied.append({**row, "status": "Blocked: destination exists"})
            continue
        source.rename(destination)
        applied.append({**row, "status": "Renamed"})
    completed = {**result, "headline": "Invoice library renamed successfully", "summary": f"{sum(r['status'] == 'Renamed' for r in applied)} invoice files were renamed and recorded.", "rows": applied, "can_apply": False}
    return _write_artifacts(base, completed)


def _base_result(headline: str, summary: str, metrics: list[dict], rows: list[dict], columns: list[dict], insights: list[dict], artifacts: list[dict] | None = None, can_apply: bool = False) -> dict:
    return {"headline": headline, "summary": summary, "metrics": metrics, "rows": rows, "columns": columns, "insights": insights, "artifacts": artifacts or [], "can_apply": can_apply}


def _csv_cleaner(base: Path, source: Path, options: dict) -> dict:
    rows = core.read_csv(source); cleaned=[]; seen=set(); blanks=duplicates=changes=0
    for row in rows:
        if all(not str(value).strip() for value in row.values()): blanks += 1; continue
        item={}
        for key,value in row.items():
            original=str(value or ""); value=original.strip()
            if "email" in key.lower(): value=value.lower()
            elif "name" in key.lower(): value=" ".join(part.capitalize() for part in value.split())
            elif "date" in key.lower():
                for fmt in ("%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%d/%m/%y"):
                    try: value=datetime.strptime(value,fmt).strftime("%Y-%m-%d"); break
                    except ValueError: pass
            elif any(word in key.lower() for word in ("spend","price","amount","total")): value=re.sub(r"[^0-9.\-]","",value)
            changes += value != original
            item[key]=value
        identity=tuple(item.values())
        business_key=(item.get("customer_id"),item.get("email")) if "customer_id" in item else identity
        if business_key in seen: duplicates += 1; continue
        seen.add(business_key); cleaned.append(item)
    destination=base/"outputs"/"clean_data.csv"; core.write_csv(destination,cleaned)
    columns=[{"key":key,"label":key.replace("_"," ").title()} for key in (list(cleaned[0]) if cleaned else [])]
    return _base_result("Your data is clean, consistent and ready",f"Converted {len(rows)} source rows into {len(cleaned)} dependable records while preserving the original file.",[
        metric("INPUT ROWS",len(rows),"reviewed locally"),metric("CLEAN ROWS",len(cleaned),"ready to use"),metric("DUPLICATES",duplicates,"removed safely"),metric("VALUES FIXED",changes,"standardised")],cleaned,columns,[insight("Original preserved","The source CSV was never changed; the cleaned export was written as a new file.","good"),insight("Rules applied",f"Removed {blanks} blank rows, normalised names, emails, dates and currency-like values."),insight("Next step","Open the clean CSV in Excel or use it as a safer import for another system.")],[{"name":"Clean CSV","path":str(destination),"description":"Production-ready cleaned data"}])


def _excel_report(base: Path, source: Path, options: dict) -> dict:
    rows=core.read_csv(source); revenues=[float(r["revenue"]) for r in rows]; grouped=Counter()
    for row in rows: grouped[row["product"]]+=float(row["revenue"])
    output=base/"reports"/"Sales_Performance_Report.xlsx"
    completed=subprocess.run([sys.executable,str(base/"generate_report.py"),str(source),"--output",str(output)],cwd=base,capture_output=True,text=True)
    if completed.returncode: raise ValueError(completed.stderr.strip() or "Excel report generation failed")
    table=[{"product":name,"revenue":money(value),"share":f"{value/sum(revenues)*100:.1f}%"} for name,value in grouped.most_common()]
    return _base_result("Executive reporting, finished",f"Built a four-sheet Excel workbook from {len(rows)} orders with dashboard KPIs, charts, audit tables and source data.",[
        metric("REVENUE",money(sum(revenues)),"total recorded"),metric("ORDERS",len(rows),"included"),metric("AVERAGE",money(sum(revenues)/len(rows)),"per order"),metric("TOP PRODUCT",grouped.most_common(1)[0][0],"by revenue")],table,[{"key":"product","label":"Product"},{"key":"revenue","label":"Revenue"},{"key":"share","label":"Share"}],[insight("Presentation ready","The workbook includes an Executive Summary designed for a meeting or client review.","good"),insight("Fully auditable","Analysis, raw data and report information remain available behind the dashboard."),insight("Refreshable workflow","Replace the CSV and run the product again whenever a new reporting period closes.")],[{"name":"Executive workbook","path":str(output),"description":"Four-sheet Excel report"}])


def _invoice_renamer(base: Path, source: Path, options: dict) -> dict:
    folder=source.parent/"files"; rows=[]; missing=collisions=0
    for mapping in core.read_csv(source):
        current=folder/mapping["current_name"]; proposed=f"{mapping['date']}_{core.safe_name(mapping['supplier'])}_{core.safe_name(mapping['invoice_number'])}{current.suffix.lower()}"; target=folder/proposed
        status="Ready"
        if not current.exists(): status="Missing source"; missing+=1
        elif target.exists(): status="Blocked: destination exists"; collisions+=1
        rows.append({"current_name":current.name,"proposed_name":target.name,"supplier":mapping["supplier"],"invoice":mapping["invoice_number"],"status":status,"source":display_path(base,current),"destination":display_path(base,target)})
    return _base_result("A clean invoice library is ready for approval",f"Prepared {len(rows)} transparent rename actions. No invoice has been changed yet.",[
        metric("INVOICES",len(rows),"mapping rows"),metric("READY",sum(r["status"]=="Ready" for r in rows),"safe to rename"),metric("MISSING",missing,"requires review"),metric("COLLISIONS",collisions,"blocked automatically")],rows,[{"key":"current_name","label":"Current file"},{"key":"proposed_name","label":"Proposed name"},{"key":"supplier","label":"Supplier"},{"key":"status","label":"Safety status"}],[insight("Approval required","The preview must be reviewed before any filename is changed.","good"),insight("Searchable convention","Every proposed name contains the invoice date, supplier and invoice number."),insight("Overwrite protection","Existing target filenames are blocked rather than replaced.")],can_apply=not missing and not collisions)


def _backup(base: Path, source: Path, options: dict) -> dict:
    snapshot=core.folder_snapshot(source); total=sum(item["bytes"] for item in snapshot.values()); output=base/"outputs"/"verified_backup.zip"; core.create_backup(source,output)
    with zipfile.ZipFile(output) as archive: manifest=json.loads(archive.read("BACKUP_MANIFEST.json")); verified=len(manifest)==len(snapshot)
    rows=[{"path":path,"size":human_size(data["bytes"]),"sha256":data["sha256"][:16]+"…"} for path,data in snapshot.items()]
    return _base_result("A verified backup is ready",f"Created a compressed archive containing {len(rows)} files and embedded a SHA-256 integrity manifest.",[
        metric("FILES",len(rows),"archived"),metric("SOURCE SIZE",human_size(total),"before compression"),metric("ARCHIVE SIZE",human_size(output.stat().st_size),"stored locally"),metric("VERIFIED","YES" if verified else "NO","manifest checked")],rows,[{"key":"path","label":"File"},{"key":"size","label":"Size"},{"key":"sha256","label":"SHA-256 fingerprint"}],[insight("Integrity built in","Every archived file has a cryptographic fingerprint stored inside the ZIP.","good"),insight("Source untouched","Creating the backup does not move, rename or delete the original folder."),insight("Recovery evidence","The embedded manifest makes later verification possible.")],[{"name":"Verified ZIP backup","path":str(output),"description":"Compressed archive with embedded manifest"}])


def _prices(base: Path, source: Path, options: dict) -> dict:
    data=core.analyse_prices(source); products=data["products"]; biggest=max(products,key=lambda r:abs(r["change_percent"]))
    rows=[{**row,"first_price":money(row["first_price"]),"latest_price":money(row["latest_price"]),"lowest_price":money(row["lowest_price"]),"change":f"{row['change_percent']:+.1f}%","signal":"BUYING OPPORTUNITY" if row["change_percent"]<0 else "PRICE INCREASE"} for row in products]
    return _base_result("Price movement is now visible",f"Analysed {data['observations']} recorded prices and isolated the changes that deserve attention.",[metric("PRODUCTS",len(products),"tracked"),metric("OBSERVATIONS",data["observations"],"analysed"),metric("LARGEST MOVE",f"{biggest['change_percent']:+.1f}%",biggest["product"]),metric("LOWEST FOUND",money(min(p["lowest_price"] for p in products)),"across history")],rows,[{"key":"product","label":"Product"},{"key":"first_price","label":"First"},{"key":"latest_price","label":"Latest"},{"key":"change","label":"Change"},{"key":"signal","label":"Signal"}],[insight("Decision support","Negative changes can indicate a buying window; positive changes can trigger supplier review.","good"),insight("Offline by design","This version analyses authorised exports and does not scrape retailer websites."),insight("Transparent evidence","First, latest and lowest prices remain visible beside every signal.")])


def _tenders(base: Path, source: Path, options: dict) -> dict:
    keywords=[word.strip() for word in str(options.get("keywords","automation,engineering,software,python,data")).split(",") if word.strip()]; threshold=float(options.get("minimum_value",1000)); rows=core.score_tenders(source,keywords,threshold)
    for row in rows: row["value_display"]=money(float(row.get("value",0))); row["recommendation"]="PRIORITY REVIEW" if row["score"]>=60 else "REVIEW" if row["score"]>=20 else "LOW FIT"
    priority=sum(r["score"]>=60 for r in rows)
    return _base_result("The strongest opportunities are ranked first",f"Scored {len(rows)} tenders against {len(keywords)} capability signals and a {money(threshold)} value threshold.",[metric("OPPORTUNITIES",len(rows),"reviewed"),metric("PRIORITY",priority,"strong matches"),metric("TOP SCORE",max((r["score"] for r in rows),default=0),"out of 100"),metric("KEYWORDS",len(keywords),"fit signals")],rows,[{"key":"title","label":"Opportunity"},{"key":"value_display","label":"Value"},{"key":"matched_keywords","label":"Matched capability"},{"key":"score","label":"Score"},{"key":"recommendation","label":"Recommendation"}],[insight("Human decision retained","Scores prioritise reading; they never replace eligibility and bid/no-bid review.","good"),insight("Explainable ranking","Every score is supported by visible keyword matches and contract value."),insight("Reusable profile",f"Current capability profile: {', '.join(keywords)}.")])


def _duplicates(base: Path, source: Path, options: dict) -> dict:
    groups=core.find_duplicates(source); reclaim=sum(group["bytes"]*(len(group["files"])-1) for group in groups); rows=[]
    for i,group in enumerate(groups,1): rows.append({"group":f"Duplicate group {i}","copies":len(group["files"]),"size_each":human_size(group["bytes"]),"potential_saving":human_size(group["bytes"]*(len(group["files"])-1)),"files":" · ".join(Path(f).name for f in group["files"]),"sha256":group["sha256"][:16]+"…"})
    return _base_result("Duplicate content has been isolated",f"Used file size and SHA-256 evidence to find {len(groups)} exact duplicate groups without deleting anything.",[metric("GROUPS",len(groups),"exact matches"),metric("EXTRA COPIES",sum(max(0,len(g["files"])-1) for g in groups),"review candidates"),metric("RECLAIMABLE",human_size(reclaim),"potential saving"),metric("DELETIONS",0,"always manual")],rows,[{"key":"group","label":"Group"},{"key":"copies","label":"Copies"},{"key":"size_each","label":"Each"},{"key":"potential_saving","label":"Potential saving"},{"key":"files","label":"Files"}],[insight("Evidence, not guesses","Files are grouped only when their cryptographic content hash matches.","good"),insight("Zero automatic deletion","The product identifies candidates but leaves final retention decisions to the owner."),insight("Efficient scan","File size is used with SHA-256 to provide reliable duplicate evidence.")])


def _documents(base: Path, source: Path, options: dict) -> dict:
    inputs=sorted(source.glob("*.txt")); output=base/"outputs"/"review_pack.txt"; core.merge_text_documents(inputs,output); text=output.read_text(); rows=[{"order":i,"document":p.name,"words":len(p.read_text().split()),"characters":len(p.read_text())} for i,p in enumerate(inputs,1)]
    return _base_result("Your review pack is assembled",f"Combined {len(inputs)} source documents into one ordered pack with clear section boundaries.",[metric("DOCUMENTS",len(inputs),"combined"),metric("WORDS",len(text.split()),"in final pack"),metric("CHARACTERS",f"{len(text):,}","preserved"),metric("SOURCE CHANGES",0,"originals untouched")],rows,[{"key":"order","label":"Order"},{"key":"document","label":"Document"},{"key":"words","label":"Words"},{"key":"characters","label":"Characters"}],[insight("Traceable structure","Each section retains its original filename as a visible heading.","good"),insight("Originals preserved","The pack is a new output; input notes are never modified."),insight("Ready for extension","The service layer can later add PDF and DOCX rendering without changing the ordering logic.")],[{"name":"Structured review pack","path":str(output),"description":"Combined plain-text delivery"}])


def _images(base: Path, source: Path, options: dict) -> dict:
    rows=core.image_manifest(source); total=sum(r["bytes"] for r in rows); hashes=Counter(r["sha256"] for r in rows); duplicates=sum(v-1 for v in hashes.values() if v>1)
    for row in rows: row["size"]=human_size(row["bytes"]); row["integrity"]=row["sha256"][:16]+"…"
    return _base_result("Your image library has a clean audit plan",f"Catalogued {len(rows)} visual assets and prepared consistent names without changing the originals.",[metric("IMAGES",len(rows),"catalogued"),metric("LIBRARY SIZE",human_size(total),"scanned"),metric("DUPLICATES",duplicates,"content matches"),metric("RENAMED",0,"preview only")],rows,[{"key":"current_name","label":"Current name"},{"key":"suggested_name","label":"Suggested name"},{"key":"size","label":"Size"},{"key":"integrity","label":"Integrity"}],[insight("Rename preview only","Suggested names are an auditable plan; this release does not rename automatically.","good"),insight("Integrity evidence","Every supported asset receives a SHA-256 fingerprint."),insight("Duplicate visibility",f"Detected {duplicates} repeated content item(s) by hash.")])


def _logs(base: Path, source: Path, options: dict) -> dict:
    data=core.analyse_log(source); severity=data["severities"]; critical=severity.get("ERROR",0)+severity.get("CRITICAL",0); rows=[{"severity":name,"events":count,"share":f"{count/max(1,sum(severity.values()))*100:.1f}%"} for name,count in sorted(severity.items(),key=lambda x:-x[1])]
    return _base_result("Operational noise has become a focused briefing",f"Reviewed {data['lines']} log lines and summarised severity plus recurring messages.",[metric("LOG LINES",data["lines"],"reviewed"),metric("ERROR EVENTS",critical,"needs attention"),metric("WARNINGS",severity.get("WARNING",0),"monitor"),metric("SEVERITIES",len(severity),"observed")],rows,[{"key":"severity","label":"Severity"},{"key":"events","label":"Events"},{"key":"share","label":"Share"}],[insight("Immediate focus",f"{critical} error or critical event(s) should be investigated first.","warning" if critical else "good"),insight("Recurring messages",str(data["top_messages"][:3]) if data["top_messages"] else "No repeated structured messages were found."),insight("Local analysis","Potentially sensitive logs never leave the computer.")])


def _quality(base: Path, source: Path, options: dict) -> dict:
    data=core.audit_csv(source); total_missing=sum(data["missing"].values()); score=max(0,100-round((total_missing+data["duplicate_rows"])/max(1,data["rows"]*max(1,data["columns"]))*100)); rows=[{"field":field,"missing":count,"completeness":f"{(data['rows']-count)/max(1,data['rows'])*100:.1f}%","status":"GOOD" if count==0 else "REVIEW"} for field,count in data["missing"].items()]
    return _base_result("Your dataset has a measurable quality baseline",f"Audited {data['rows']} rows across {data['columns']} fields and converted hidden weaknesses into an action list.",[metric("QUALITY SCORE",f"{score}/100","current baseline"),metric("ROWS",data["rows"],"audited"),metric("MISSING",total_missing,"empty values"),metric("DUPLICATES",data["duplicate_rows"],"repeated rows")],rows,[{"key":"field","label":"Field"},{"key":"missing","label":"Missing"},{"key":"completeness","label":"Completeness"},{"key":"status","label":"Status"}],[insight("Start with the weakest field",max(rows,key=lambda r:r["missing"])["field"] if rows else "No fields were available.","warning" if total_missing else "good"),insight("No silent repair","This auditor measures problems without guessing replacement values."),insight("Repeatable KPI",f"Use {score}/100 as the baseline for the next cleanup cycle.")])


def _quote(base: Path, source: Path, options: dict) -> dict:
    tax=float(options.get("tax_rate",20))/100; data=core.build_quote(source,tax); rows=[{**r,"unit_price_display":money(float(r["unit_price"])),"line_total_display":money(r["line_total"])} for r in data["items"]]
    return _base_result("A clear commercial quote is ready",f"Calculated {len(rows)} line items, tax and final price with a complete arithmetic trail.",[metric("SUBTOTAL",money(data["subtotal"]),"before tax"),metric("TAX",money(data["tax"]),f"{tax*100:.0f}% rate"),metric("TOTAL",money(data["total"]),"quoted value"),metric("ITEMS",len(rows),"priced")],rows,[{"key":"description","label":"Description"},{"key":"quantity","label":"Quantity"},{"key":"unit_price_display","label":"Unit price"},{"key":"line_total_display","label":"Line total"}],[insight("Arithmetic verified","Every line total is quantity multiplied by unit price before tax is added.","good"),insight("Transparent price","Subtotal, tax and final total are kept separate for customer clarity."),insight("Reusable input","Update the CSV to create another quote without editing the calculation code.")])


def _expenses(base: Path, source: Path, options: dict) -> dict:
    rules={"Software":["github","adobe","microsoft","hosting"],"Travel":["rail","uber","fuel","hotel"],"Office":["stationery","paper","printer"],"Marketing":["advert","canva","promotion"]}; data=core.expense_summary(source,rules); total=sum(data["totals"].values()); rows=[{**r,"amount_display":money(float(r["amount"])),"share":f"{float(r['amount'])/max(total,1)*100:.1f}%"} for r in data["transactions"]]; top=max(data["totals"],key=data["totals"].get)
    return _base_result("Spending is categorised and explainable",f"Applied transparent keyword rules to {len(rows)} transactions and produced a category-level view.",[metric("TOTAL SPEND",money(total),"reviewed"),metric("TRANSACTIONS",len(rows),"categorised"),metric("CATEGORIES",len(data["totals"]),"used"),metric("TOP CATEGORY",top,money(data["totals"][top]))],rows,[{"key":"date","label":"Date"},{"key":"description","label":"Description"},{"key":"amount_display","label":"Amount"},{"key":"category","label":"Category"},{"key":"share","label":"Share"}],[insight("Explainable rules","Categories come from visible keywords rather than an opaque model.","good"),insight("Review Other",f"{data['totals'].get('Other',0):.2f} remains uncategorised and may justify a new rule."),insight("Finance-ready export","The transaction table preserves source descriptions and adds the chosen category.")])


def _inventory(base: Path, source: Path, options: dict) -> dict:
    plan=core.reorder_plan(source); urgent=[r for r in plan if r["status"]=="REORDER"]; units=sum(r["recommended_order"] for r in urgent)
    for row in plan: row["coverage_days"]=round(float(row["stock"])/max(float(row["daily_demand"]),.0001),1)
    return _base_result("Purchasing priorities are clear",f"Calculated reorder points from demand, lead time and safety stock for {len(plan)} inventory items.",[metric("SKUS",len(plan),"reviewed"),metric("REORDER NOW",len(urgent),"below threshold"),metric("UNITS TO BUY",f"{units:g}","recommended"),metric("HEALTHY",len(plan)-len(urgent),"no action")],plan,[{"key":"sku","label":"SKU"},{"key":"stock","label":"Stock"},{"key":"coverage_days","label":"Days cover"},{"key":"reorder_point","label":"Reorder point"},{"key":"recommended_order","label":"Order quantity"},{"key":"status","label":"Decision"}],[insight("Demand-led recommendation","Orders are based on expected lead-time demand plus safety stock.","good"),insight("Immediate action",f"{len(urgent)} SKU(s) currently require a purchase decision.","warning" if urgent else "good"),insight("Transparent formula","Reorder point = daily demand × lead days + safety stock.")])


def _schedule(base: Path, source: Path, options: dict) -> dict:
    events=core.read_csv(source); conflicts=core.find_schedule_conflicts(source); minutes=0
    for c in conflicts: minutes += int((datetime.fromisoformat(c["overlap_end"])-datetime.fromisoformat(c["overlap_start"])).total_seconds()/60); c["overlap"]=f"{c['overlap_start']} → {c['overlap_end']}"
    return _base_result("Schedule risk has been isolated",f"Compared {len(events)} events and found {len(conflicts)} overlapping commitment pair(s).",[metric("EVENTS",len(events),"checked"),metric("CONFLICTS",len(conflicts),"overlaps"),metric("OVERLAP",f"{minutes} min","total conflict time"),metric("CLEAR",max(0,len(events)-len({c['event_a'] for c in conflicts}|{c['event_b'] for c in conflicts})),"unaffected events")],conflicts,[{"key":"event_a","label":"First event"},{"key":"event_b","label":"Conflicting event"},{"key":"overlap","label":"Overlap window"}],[insight("Resolve before booking",f"{len(conflicts)} conflict pair(s) need an owner decision.","warning" if conflicts else "good"),insight("Exact overlap windows","The report identifies the shared time, not merely events on the same day."),insight("No calendar write access","This version audits an authorised export and changes no calendar events.")])


def _monitor(base: Path, source: Path, options: dict) -> dict:
    current=core.folder_snapshot(source); baseline_path=base/"outputs"/"baseline_snapshot.json"; previous=json.loads(baseline_path.read_text()) if baseline_path.exists() else {}; comparison=core.compare_snapshots(previous,current) if previous else {"added":list(current),"removed":[],"changed":[]}; baseline_path.parent.mkdir(parents=True,exist_ok=True); baseline_path.write_text(json.dumps(current,indent=2)); rows=[]
    for status in ("added","changed","removed"):
        rows.extend({"path":path,"change":status.upper(),"evidence":(current.get(path) or previous.get(path) or {}).get("sha256","")[:16]+"…"} for path in comparison[status])
    return _base_result("A cryptographic change record is ready",f"Compared the current folder against the previous local baseline and recorded every added, changed or removed file.",[metric("FILES",len(current),"current snapshot"),metric("ADDED",len(comparison["added"]),"since baseline"),metric("CHANGED",len(comparison["changed"]),"content differs"),metric("REMOVED",len(comparison["removed"]),"no longer present")],rows,[{"key":"path","label":"File"},{"key":"change","label":"Change"},{"key":"evidence","label":"Hash evidence"}],[insight("Baseline refreshed","The current snapshot is now the reference point for the next run.","good"),insight("Content-aware monitoring","Changed status is driven by size and SHA-256, not timestamp alone."),insight("Local chain of evidence","The baseline remains in the product output folder.")],[{"name":"Baseline snapshot","path":str(baseline_path),"description":"Cryptographic folder state"}])


def _handover(base: Path, source: Path, options: dict) -> dict:
    output=base/"outputs"/"client_handover.zip"; result=core.package_handover(source,output); snapshot=core.folder_snapshot(source); rows=[{"path":path,"size":human_size(data["bytes"]),"sha256":data["sha256"][:16]+"…"} for path,data in snapshot.items()]
    return _base_result("Your client handover is sealed and verified",f"Validated required files, packaged {result['files']} items and fingerprinted the final delivery archive.",[metric("FILES",result["files"],"packaged"),metric("ARCHIVE",human_size(output.stat().st_size),"delivery size"),metric("CHECKSUM",result["sha256"][:12]+"…","archive identity"),metric("VALIDATION","PASSED","README present")],rows,[{"key":"path","label":"Delivered file"},{"key":"size","label":"Size"},{"key":"sha256","label":"Integrity"}],[insight("Delivery gate passed","Required handover documentation was present before packaging.","good"),insight("Tamper evidence","The final ZIP and every source file have cryptographic fingerprints."),insight("Professional handoff","One archive reduces missing-file risk and simplifies customer receipt.")],[{"name":"Client handover ZIP","path":str(output),"description":"Validated delivery archive"}])


def _sla(base: Path, source: Path, options: dict) -> dict:
    rows=core.read_csv(source); data=core.sla_dashboard(source); breaches=[r for r in rows if r.get("sla_met","").lower() not in {"yes","true","1"}]
    for row in rows: row["resolution_display"]=f"{float(row['resolution_hours']):.1f} h"; row["status"]="MET" if row not in breaches else "BREACHED"
    return _base_result("Service performance is visible",f"Converted {len(rows)} ticket records into an executive SLA performance view.",[metric("SLA MET",f"{data['sla_met_percent']:.1f}%","compliance"),metric("TICKETS",data["tickets"],"reviewed"),metric("AVERAGE",f"{data['average_resolution_hours']:.1f} h","resolution"),metric("BREACHES",len(breaches),"needs review")],rows,[{"key":"ticket","label":"Ticket"},{"key":"resolution_display","label":"Resolution"},{"key":"status","label":"SLA status"}],[insight("Breach focus",f"{len(breaches)} ticket(s) missed SLA and should be reviewed for cause.","warning" if breaches else "good"),insight("Balanced measure",f"Median resolution is {data['median_resolution_hours']:.1f} hours, reducing distortion from outliers."),insight("Executive-ready KPI",f"Current compliance is {data['sla_met_percent']:.1f}% across the supplied period.")])


def _leads(base: Path, source: Path, options: dict) -> dict:
    rows=core.lead_ranker(source); high=sum(r["priority"]=="High" for r in rows); pipeline=sum(float(r.get("budget",0)) for r in rows)
    for index,row in enumerate(rows,1): row["rank"]=index; row["budget_display"]=money(float(row.get("budget",0))); row["next_action"]="Reply today" if row["priority"]=="High" else "Qualify" if row["priority"]=="Medium" else "Nurture"
    return _base_result("The best leads are at the top",f"Ranked {len(rows)} enquiries using visible budget, urgency and fit rules.",[metric("PIPELINE",money(pipeline),"stated budgets"),metric("LEADS",len(rows),"ranked"),metric("HIGH PRIORITY",high,"reply first"),metric("TOP SCORE",rows[0]["score"] if rows else 0,"out of 100")],rows,[{"key":"rank","label":"Rank"},{"key":"client","label":"Client"},{"key":"budget_display","label":"Budget"},{"key":"priority","label":"Priority"},{"key":"score","label":"Score"},{"key":"next_action","label":"Next action"}],[insight("Speed where it matters",f"{high} high-priority lead(s) deserve the fastest response.","good"),insight("Explainable score","Strong fit contributes 40 points; high urgency and sufficient budget contribute 30 each."),insight("Decision support, not autopilot","A salesperson retains the final decision and relationship context.")])


def _write_artifacts(base: Path, result: dict) -> dict:
    output=base/"outputs"; output.mkdir(parents=True,exist_ok=True)
    if result.get("rows"):
        csv_path=output/"executive_result.csv"; fields=list(result["rows"][0]); core.write_csv(csv_path,[{k:v for k,v in row.items() if not isinstance(v,(dict,list))} for row in result["rows"]],fields=[f for f in fields if not isinstance(result["rows"][0].get(f),(dict,list))]); result.setdefault("artifacts",[]).append({"name":"CSV evidence","path":str(csv_path),"description":"Reviewable result table"})
    elif (output/"executive_result.csv").exists():
        (output/"executive_result.csv").unlink()
    report=output/"executive_report.html"; report.write_text(_report_html(result),encoding="utf-8"); result.setdefault("artifacts",[]).append({"name":"Executive report","path":str(report),"description":"Shareable local summary"}); result["report_url"]="/report"
    for artifact in result.get("artifacts", []):
        artifact["path"] = display_path(base, Path(artifact["path"]))
    json_path=output/"executive_result.json"
    json_path.write_text(json.dumps({k:v for k,v in result.items() if k!="report_url"},indent=2,default=str),encoding="utf-8")
    return result


def display_path(base: Path, path: Path) -> str:
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def _report_html(result: dict) -> str:
    metrics="".join(f"<article><small>{escape(m['label'])}</small><strong>{escape(m['value'])}</strong><span>{escape(m['note'])}</span></article>" for m in result.get("metrics",[]))
    insights="".join(f"<div><b>{escape(i['title'])}</b><p>{escape(i['body'])}</p></div>" for i in result.get("insights",[]))
    columns=result.get("columns",[]); heads="".join(f"<th>{escape(c['label'])}</th>" for c in columns); body="".join("<tr>"+"".join(f"<td>{escape(str(row.get(c['key'],'')))}</td>" for c in columns)+"</tr>" for row in result.get("rows",[])[:100])
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>{escape(result['product_name'])} Report</title><style>:root{{--n:#142b3a;--g:#b79a62;--p:#f6f8f9;--s:#60737e;--l:#dce3e6}}*{{box-sizing:border-box}}body{{margin:0;background:var(--p);color:var(--n);font:14px Inter,Aptos,Arial}}header{{padding:60px 7vw;background:var(--n);color:#fff}}header small{{color:var(--g);letter-spacing:.2em;font-weight:700}}h1{{font:48px Georgia;margin:18px 0 8px}}header p{{color:#c6d0d5}}main{{max-width:1260px;margin:-28px auto 60px;padding:0 25px}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}article,.panel{{background:#fff;border:1px solid var(--l);padding:24px}}article small,article strong,article span{{display:block}}article small{{font-size:9px;letter-spacing:.12em;color:var(--s)}}article strong{{font:28px Georgia;margin:12px 0}}article span{{font-size:10px;color:var(--s)}}.panel{{margin-top:16px}}h2{{font:22px Georgia}}.insights{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.insights div{{border-left:2px solid var(--g);padding:5px 18px}}.insights p{{color:var(--s);line-height:1.6}}table{{border-collapse:collapse;width:100%}}th,td{{padding:12px;border-bottom:1px solid var(--l);text-align:left}}th{{font-size:9px;letter-spacing:.1em;background:#edf1f2}}@media(max-width:800px){{.metrics,.insights{{grid-template-columns:1fr 1fr}}}}@media(max-width:520px){{.metrics,.insights{{grid-template-columns:1fr}}}}</style></head><body><header><small>COOKE AUTOMATION SYSTEMS · PRODUCT {escape(result['product_id'])}</small><h1>{escape(result['headline'])}</h1><p>{escape(result['summary'])}</p></header><main><section class='metrics'>{metrics}</section><section class='panel'><h2>Executive interpretation</h2><div class='insights'>{insights}</div></section><section class='panel'><h2>Evidence</h2><div style='overflow:auto'><table><thead><tr>{heads}</tr></thead><tbody>{body}</tbody></table></div></section></main></body></html>"""
