import unittest
from pathlib import Path

from cooke_systems.product_runtime import PRODUCTS, analyse, apply_preview


ROOT = Path(__file__).resolve().parents[1]


class ProductRuntimeTests(unittest.TestCase):
    def test_every_guided_product_generates_real_evidence(self):
        for product_id, (_, _, _, default_input) in PRODUCTS.items():
            with self.subTest(product=product_id):
                base = next(ROOT.glob(f"{int(product_id):02d}_*"))
                result = analyse(product_id, base, default_input, {})
                self.assertEqual(result["product_id"], product_id)
                self.assertEqual(len(result["metrics"]), 4)
                self.assertTrue(result["headline"])
                self.assertTrue(result["summary"])
                self.assertTrue(result["insights"])
                self.assertTrue((base / "outputs" / "executive_result.json").exists())
                self.assertTrue((base / "outputs" / "executive_report.html").exists())

    def test_every_guided_product_has_launchable_entrypoint(self):
        for product_id in PRODUCTS:
            with self.subTest(product=product_id):
                base = next(ROOT.glob(f"{int(product_id):02d}_*"))
                self.assertTrue((base / "app.py").exists())
                self.assertIn(f'launch("{product_id}"', (base / "app.py").read_text())

    def test_invoice_rename_requires_and_honours_an_approved_preview(self):
        import csv
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            files = base / "sample_data" / "files"
            files.mkdir(parents=True)
            (files / "invoice.pdf").write_text("invoice")
            mapping = base / "sample_data" / "input.csv"
            with mapping.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["current_name", "date", "supplier", "invoice_number"])
                writer.writeheader()
                writer.writerow({"current_name": "invoice.pdf", "date": "2026-07-13", "supplier": "Aero Parts", "invoice_number": "INV-7"})
            preview = analyse("004", base, str(mapping), {})
            self.assertTrue(preview["can_apply"])
            self.assertTrue((files / "invoice.pdf").exists())
            result = apply_preview("004", base, preview)
            self.assertEqual(result["rows"][0]["status"], "Renamed")
            self.assertTrue((files / "2026-07-13_Aero_Parts_INV_7.pdf").exists())


if __name__ == "__main__":
    unittest.main()
