from pathlib import Path
import pandas as pd

INPUT_FILE = Path("sample_data/sample_sales.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "sales_report.xlsx"

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(INPUT_FILE)
    summary = df.groupby("category", as_index=False).agg(total_revenue=("revenue","sum"), orders=("order_id","count"))
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Raw Data")
        summary.to_excel(writer, index=False, sheet_name="Summary")
    print(f"Created {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
