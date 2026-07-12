from pathlib import Path
import argparse
from src.report import generate_report

def main():
    parser = argparse.ArgumentParser(description="Generate a premium Excel sales report.")
    parser.add_argument("input", nargs="?", default="sample_data/sample_sales.csv")
    parser.add_argument("--output", default="reports/Sales_Performance_Report.xlsx")
    args = parser.parse_args()
    path = generate_report(Path(args.input), Path(args.output))
    print(f"Report created: {path.resolve()}")

if __name__ == "__main__":
    main()
