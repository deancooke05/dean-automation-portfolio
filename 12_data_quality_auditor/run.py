from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cooke_systems import core

PRODUCT = 'quality'
BASE = Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description='Reports missing data, duplicate rows and structural CSV issues.')
    parser.add_argument("input", nargs="?", default=str(BASE/"sample_data"/"input.csv"))
    parser.add_argument("--output", default=str(BASE/"outputs"/"result.json"))
    parser.add_argument("--apply", action="store_true", help="Apply file changes for products that support execution; preview is the default.")
    args=parser.parse_args(); source=Path(args.input); output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists() and (BASE/"sample_data"/"input").exists(): source=BASE/"sample_data"/"input"
    if PRODUCT=="organise": result=core.organise_files(source, output.parent/"organised", args.apply)
    elif PRODUCT=="invoice": result=core.rename_invoices(source.parent/"files", source, args.apply)
    elif PRODUCT=="backup": result={"archive":str(core.create_backup(source, output.with_suffix(".zip")))}
    elif PRODUCT=="prices": result=core.analyse_prices(source)
    elif PRODUCT=="tenders": result=core.score_tenders(source,["automation","engineering","software"],1000)
    elif PRODUCT=="duplicates": result=core.find_duplicates(source)
    elif PRODUCT=="documents": result={"output":str(core.merge_text_documents(sorted(source.glob("*.txt")),output.with_suffix(".txt")))}
    elif PRODUCT=="images": result=core.image_manifest(source)
    elif PRODUCT=="logs": result=core.analyse_log(source)
    elif PRODUCT=="quality": result=core.audit_csv(source)
    elif PRODUCT=="quote": result=core.build_quote(source)
    elif PRODUCT=="expenses": result=core.expense_summary(source,{"Software":["github","adobe","microsoft"],"Travel":["rail","uber","fuel"],"Office":["stationery","paper"]})
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
