import tempfile
import unittest
from pathlib import Path

from src.service import OrganiserService


class OrganiserServiceTests(unittest.TestCase):
    def test_preview_is_non_destructive_and_explains_every_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "incoming"
            source.mkdir()
            (source / "report.pdf").write_text("report")
            service = OrganiserService(base)

            preview = service.preview(str(source), str(base / "organised"))

            self.assertTrue((source / "report.pdf").exists())
            self.assertEqual(preview["summary"]["files"], 1)
            self.assertEqual(preview["actions"][0]["destination_display"], "Documents/report.pdf")
            self.assertTrue((base / "outputs" / "preview_manifest.json").exists())

    def test_apply_requires_preview(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "preview"):
                OrganiserService(Path(temporary)).apply()

    def test_apply_copies_files_and_returns_report_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "incoming"
            source.mkdir()
            (source / "data.csv").write_text("a,b\n1,2")
            destination = base / "organised"
            service = OrganiserService(base)
            service.preview(str(source), str(destination))

            result = service.apply()

            self.assertEqual(result["summary"]["completed"], 1)
            self.assertEqual(result["report_url"], "/report")
            self.assertTrue((destination / "Spreadsheets" / "data.csv").exists())
            self.assertTrue((source / "data.csv").exists())


if __name__ == "__main__":
    unittest.main()
