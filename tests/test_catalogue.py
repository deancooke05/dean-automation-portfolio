import json
import tempfile
import unittest
from pathlib import Path

from cooke_systems import core


ROOT = Path(__file__).resolve().parents[1]


class CatalogueTests(unittest.TestCase):
    def sample(self, folder):
        return ROOT / folder / "sample_data" / "input.csv"

    def test_prices(self):
        result = core.analyse_prices(self.sample("06_price_tracker_demo"))
        self.assertEqual(result["observations"], 4)
        self.assertEqual(len(result["products"]), 2)

    def test_tender_ranking(self):
        result = core.score_tenders(self.sample("07_tenderscout_case_study"), ["automation", "engineering", "software"], 1000)
        self.assertGreaterEqual(result[0]["score"], result[-1]["score"])

    def test_quote_reconciles(self):
        result = core.build_quote(self.sample("13_quote_builder"))
        self.assertAlmostEqual(result["total"], result["subtotal"] + result["tax"], 2)

    def test_schedule_conflict(self):
        result = core.find_schedule_conflicts(self.sample("16_schedule_conflict_checker"))
        self.assertEqual(len(result), 1)

    def test_inventory(self):
        result = core.reorder_plan(self.sample("15_inventory_reorder_planner"))
        self.assertEqual(result[0]["status"], "REORDER")

    def test_data_quality(self):
        result = core.audit_csv(self.sample("12_data_quality_auditor"))
        self.assertEqual(result["duplicate_rows"], 1)
        self.assertEqual(result["missing"]["name"], 2)

    def test_backup_contains_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"; source.mkdir(); (source / "file.txt").write_text("verified")
            archive = core.create_backup(source, Path(temporary) / "backup.zip")
            self.assertTrue(archive.exists())

    def test_snapshot_change_detection(self):
        before = {"a.txt": {"bytes": 1, "sha256": "a"}}
        after = {"a.txt": {"bytes": 2, "sha256": "b"}, "b.txt": {"bytes": 1, "sha256": "c"}}
        result = core.compare_snapshots(before, after)
        self.assertEqual(result["changed"], ["a.txt"])
        self.assertEqual(result["added"], ["b.txt"])

    def test_sla(self):
        result = core.sla_dashboard(self.sample("19_service_sla_dashboard"))
        self.assertEqual(result["tickets"], 3)
        self.assertEqual(result["sla_met_percent"], 66.7)

    def test_lead_ranking(self):
        result = core.lead_ranker(self.sample("20_client_lead_ranker"))
        self.assertEqual(result[0]["priority"], "High")


if __name__ == "__main__":
    unittest.main()
