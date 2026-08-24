import json
import tempfile
import unittest
from pathlib import Path

from walkforwardlab.cli import main

DATA = Path(__file__).parents[1] / "walkforwardlab" / "data"


class CliTests(unittest.TestCase):
    def test_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/"report.json"
            self.assertEqual(main([str(DATA/"demo_config.json"), str(DATA/"demo_bars.csv"), "--output", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text())["schema"], "walkforwardlab/report-1")
