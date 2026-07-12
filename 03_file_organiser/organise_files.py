from pathlib import Path
import shutil

SOURCE = Path("sample_messy_folder")
OUTPUT = Path("organised_output")
CATEGORIES = {
    "Documents": [".pdf", ".docx", ".txt"],
    "Images": [".jpg", ".jpeg", ".png"],
    "Spreadsheets": [".csv", ".xlsx"],
    "Code": [".py", ".js", ".html", ".css"],
}

def category(path):
    for name, exts in CATEGORIES.items():
        if path.suffix.lower() in exts:
            return name
    return "Other"

def main():
    OUTPUT.mkdir(exist_ok=True)
    for file in SOURCE.iterdir():
        if file.is_file():
            dest = OUTPUT / category(file)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dest / file.name)
    print(f"Organised files into {OUTPUT}")

if __name__ == "__main__":
    main()
