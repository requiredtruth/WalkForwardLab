import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from walkforwardlab.core import LabError, load_bars, parse_config
from walkforwardlab.engine import position, run

DATA = Path(__file__).parents[1] / "walkforwardlab" / "data"


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((DATA/"demo_config.json").read_text())
        self.bars = load_bars(str(DATA/"demo_bars.csv"))

    def test_builds_nonoverlapping_embargoed_folds(self):
        report = run(parse_config(self.raw), self.bars)
        self.assertEqual(report["aggregate"]["fold_count"], 4)
        for left, right in zip(report["folds"], report["folds"][1:]):
            self.assertLess(left["test"]["end"], right["test"]["start"])
            self.assertEqual(left["embargo"]["bars"], 2)
        self.assertEqual(report["claims"], "historical_measurement_only")

    def test_signal_is_causal(self):
        before = position(self.bars, 10, 3, parse_config(self.raw).thresholds[0], "momentum")
        changed = copy.deepcopy(self.bars)
        changed[11] = type(changed[11])(changed[11].timestamp, changed[11].close * 100)
        self.assertEqual(before, position(changed, 10, 3, parse_config(self.raw).thresholds[0], "momentum"))

    def test_report_is_deterministic(self):
        config = parse_config(self.raw)
        self.assertEqual(run(config, self.bars), run(config, copy.deepcopy(self.bars)))

    def test_rejects_overlapping_tests(self):
        self.raw["step_size"] = 4
        with self.assertRaisesRegex(LabError, "overlapping"):
            parse_config(self.raw)

    def test_rejects_insufficient_bars(self):
        with self.assertRaisesRegex(LabError, "not enough bars"):
            run(parse_config(self.raw), self.bars[:20])

    def test_rejects_bad_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"bad.csv"; path.write_text("timestamp,open\n2026-01-01T00:00:00Z,1\n")
            with self.assertRaisesRegex(LabError, "header"):
                load_bars(str(path))

    def test_rejects_duplicate_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"bad.csv"
            path.write_text("timestamp,close\n2026-01-01T00:00:00Z,1\n2026-01-01T00:00:00Z,2\n")
            with self.assertRaisesRegex(LabError, "strictly increase"):
                load_bars(str(path))
