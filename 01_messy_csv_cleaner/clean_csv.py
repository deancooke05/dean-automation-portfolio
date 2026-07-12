import csv
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path("sample_data/messy_customers.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "clean_customers.csv"
SUMMARY_FILE = OUTPUT_DIR / "cleaning_summary.txt"

def normalise_name(value):
    return " ".join(part.capitalize() for part in value.strip().split())

def normalise_email(value):
    return value.strip().lower()

def normalise_date(value):
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return value

def is_blank_row(row):
    return all(str(value).strip() == "" for value in row.values())

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    with INPUT_FILE.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    cleaned, seen = [], set()
    blanks = duplicates = 0

    for row in rows:
        if is_blank_row(row):
            blanks += 1
            continue

        clean = {
            "customer_id": row.get("customer_id", "").strip(),
            "name": normalise_name(row.get("name", "")),
            "email": normalise_email(row.get("email", "")),
            "date_joined": normalise_date(row.get("date_joined", "")),
            "total_spend": row.get("total_spend", "").replace("£", "").strip(),
        }

        key = (clean["customer_id"], clean["email"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        cleaned.append(clean)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(cleaned[0].keys()))
        writer.writeheader()
        writer.writerows(cleaned)

    SUMMARY_FILE.write_text(
        f"CSV Cleaning Summary\nInput rows: {len(rows)}\nClean rows: {len(cleaned)}\n"
        f"Blank rows removed: {blanks}\nDuplicate rows removed: {duplicates}\n",
        encoding="utf-8"
    )
    print(f"Created {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
