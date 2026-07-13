import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.engine import build_plan, execute_plan, undo_manifest, write_manifest


class FileOrganiserTests(unittest.TestCase):
    def test_classifies_and_preserves_sources_in_copy_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source"; destination = root / "out"; source.mkdir()
            (source / "report.pdf").write_text("report"); (source / "data.csv").write_text("a,b")
            plan = build_plan(source, destination)
            completed = execute_plan(plan)
            self.assertEqual(completed.categories, {"Documents": 1, "Spreadsheets": 1})
            self.assertTrue((source / "report.pdf").exists())
            self.assertTrue((destination / "Documents" / "report.pdf").exists())

    def test_collision_gets_safe_suffix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source"; destination = root / "out"; source.mkdir()
            (source / "notes.txt").write_text("new")
            target = destination / "Documents"; target.mkdir(parents=True); (target / "notes.txt").write_text("existing")
            action = build_plan(source, destination).actions[0]
            self.assertTrue(action.collision)
            self.assertEqual(Path(action.destination).name, "notes_2.txt")

    def test_move_manifest_can_be_undone(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source"; destination = root / "out"; source.mkdir()
            original = source / "notes.txt"; original.write_text("important")
            completed = execute_plan(build_plan(source, destination, mode="move"))
            manifest = write_manifest(completed, root / "manifest.json")
            result = undo_manifest(manifest)
            self.assertEqual(result["restored"], 1)
            self.assertTrue(original.exists())

    def test_destination_inside_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary); nested = source / "output"
            with self.assertRaises(ValueError):
                build_plan(source, nested)


if __name__ == "__main__":
    unittest.main()
