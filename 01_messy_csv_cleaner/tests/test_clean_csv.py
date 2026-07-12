import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "clean_csv.py"

spec = importlib.util.spec_from_file_location("clean_csv", SCRIPT_PATH)
clean_csv = importlib.util.module_from_spec(spec)
sys.modules["clean_csv"] = clean_csv
spec.loader.exec_module(clean_csv)


class TestCSVCleaningFunctions(unittest.TestCase):

    def test_normalise_name(self):
        self.assertEqual(clean_csv.normalise_name("  jOhN   sMiTh  "), "John Smith")

    def test_normalise_email(self):
        self.assertEqual(clean_csv.normalise_email("  JOHN@MAIL.COM "), "john@mail.com")

    def test_normalise_date_slash_format(self):
        self.assertEqual(clean_csv.normalise_date("01/02/2024"), "2024-02-01")

    def test_normalise_date_dash_format(self):
        self.assertEqual(clean_csv.normalise_date("02-02-2024"), "2024-02-02")

    def test_normalise_date_iso_format(self):
        self.assertEqual(clean_csv.normalise_date("2024-02-03"), "2024-02-03")

    def test_unknown_date_is_preserved(self):
        self.assertEqual(clean_csv.normalise_date("not-a-date"), "not-a-date")

    def test_blank_row_detection(self):
        row = {"customer_id": "", "name": " ", "email": "", "date_joined": "", "total_spend": ""}
        self.assertTrue(clean_csv.is_blank_row(row))

    def test_non_blank_row_detection(self):
        row = {"customer_id": "1001", "name": "", "email": "", "date_joined": "", "total_spend": ""}
        self.assertFalse(clean_csv.is_blank_row(row))


if __name__ == "__main__":
    unittest.main()
