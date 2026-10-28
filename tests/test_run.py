"""Gate tests for traptest/run.py — no network, no purchase, ever."""
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.run import check_gates, main


class TestGates(unittest.TestCase):
    def test_before_window_refused_even_with_marker(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "LIVE-ACTIVATED"
            marker.write_text("activated")
            ok, reason = check_gates(today=date(2026, 10, 27), marker=marker)
            self.assertFalse(ok)
            self.assertIn("GATE REFUSED", reason)

    def test_window_date_without_marker_refused(self):
        with tempfile.TemporaryDirectory() as d:
            ok, reason = check_gates(today=date(2026, 11, 1),
                                     marker=Path(d) / "LIVE-ACTIVATED")
            self.assertFalse(ok)
            self.assertIn("marker missing", reason)

    def test_both_gates_pass_on_opening_day(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "LIVE-ACTIVATED"
            marker.write_text("activated")
            ok, _ = check_gates(today=date(2026, 11, 1), marker=marker)
            self.assertTrue(ok)

    def test_main_refuses_before_window_and_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "LIVE-ACTIVATED"
            marker.write_text("activated")
            code = main(["--marker", str(marker)], today=date(2026, 10, 31))
            self.assertEqual(code, 2)

    def test_main_with_gates_but_no_traps_makes_no_purchase(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "LIVE-ACTIVATED"
            marker.write_text("activated")
            # No --traps/--miner: must exit 3 without any network purchase.
            code = main(["--marker", str(marker)], today=date(2026, 11, 1))
            self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
