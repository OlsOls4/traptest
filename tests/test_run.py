"""Gate tests for traptest/run.py — no network, no purchase, ever."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.providers import _HttpResponse
from traptest.run import check_gates, main

INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
ROOT = Path(__file__).resolve().parent.parent


class _MinersTransport:
    """Fake catalogue fetch only (free GET, no purchase)."""

    def __init__(self):
        self.calls = []

    def __call__(self, method, url, body, headers):
        self.calls.append((method, url))
        return _HttpResponse(200, json.dumps({"miners": [
            {"id": "9002", "name": "TxLens"},
            {"id": "8453", "name": "Truvian"},
        ]}).encode(), {})


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


class TestGateScoping(unittest.TestCase):
    """(13 Nov 2026) --list-miners and --dry-run bypass the marker;
    a real purchase still requires it."""

    def test_check_gates_without_marker_requirement(self):
        with tempfile.TemporaryDirectory() as d:
            ok, reason = check_gates(today=date(2026, 11, 13),
                                     marker=Path(d) / "LIVE-ACTIVATED",
                                     require_marker=False)
            self.assertTrue(ok)
            self.assertIn("marker not required", reason)

    def test_check_gates_still_requires_marker_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            ok, _ = check_gates(today=date(2026, 11, 13),
                                marker=Path(d) / "LIVE-ACTIVATED")
            self.assertFalse(ok)

    def test_list_miners_succeeds_with_no_marker_and_no_key(self):
        # Fresh-clone simulation: no marker file, no key file.
        with tempfile.TemporaryDirectory() as d:
            t = _MinersTransport()
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--list-miners",
                             "--marker", str(Path(d) / "LIVE-ACTIVATED")],
                            today=date(2026, 11, 13), transport=t)
            self.assertEqual(code, 0)
            self.assertIn("2 live miners", out.getvalue())
            self.assertEqual(len(t.calls), 1)  # one free catalogue GET

    def test_real_purchase_still_refused_without_marker(self):
        with tempfile.TemporaryDirectory() as d:
            t = _MinersTransport()
            code = main(["--marker", str(Path(d) / "LIVE-ACTIVATED"),
                         "--traps", str(ROOT / "traps-frozen-2026-11-06.json"),
                         "--providers", "9002",
                         "--key", str(Path(d) / "no-such.key"),
                         "--out", str(Path(d) / "out.json")],
                        today=date(2026, 11, 13), transport=t)
            self.assertEqual(code, 2)
            self.assertEqual(t.calls, [])  # refused before any network


if __name__ == "__main__":
    unittest.main()
