"""Mock-fixture tests only — these are NOT event evidence."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.traps import Trap, validate_trap_set
from traptest.scoring import score_answer
from traptest.leaderboard import Leaderboard


def trap():
    # MOCK fixture: a made-up hash/ground truth for framework testing only.
    return Trap("mock-1", "ONCHAIN_TX_LOOKUP_GENERAL",
                "0x" + "ab" * 32,
                expected_status="confirmed",
                expected_from="0xAAA", expected_to="0xBBB",
                expected_value="100", expected_block=123)


class TestScoring(unittest.TestCase):
    def test_pass_when_all_fields_match(self):
        s = score_answer(trap(), "miner-1",
                         {"status": "confirmed", "from": "0xaaa",
                          "to": "0xBBB", "value": "100", "block": 123},
                         cost_usd=0.01, receipt_present=True)
        self.assertTrue(s.passed)
        self.assertTrue(s.receipt_present)

    def test_status_mismatch_fails_outright(self):
        s = score_answer(trap(), "miner-1",
                         {"status": "reverted", "from": "0xaaa",
                          "to": "0xBBB", "value": "100", "block": 123})
        self.assertFalse(s.passed)

    def test_missing_field_is_a_failure_not_a_pass(self):
        s = score_answer(trap(), "miner-1",
                         {"status": "confirmed", "from": "0xaaa"})
        self.assertFalse(s.passed)

    def test_trap_validation(self):
        with self.assertRaises(ValueError):
            validate_trap_set([])
        with self.assertRaises(ValueError):
            validate_trap_set([trap(), trap()])  # duplicate id

    def test_leaderboard_ranking(self):
        lb = Leaderboard()
        lb.add(score_answer(trap(), "b",
                            {"status": "confirmed", "from": "0xaaa",
                             "to": "0xBBB", "value": "100", "block": 123},
                            cost_usd=0.02))
        lb.add(score_answer(trap(), "a",
                            {"status": "reverted", "from": "0xaaa",
                             "to": "0xBBB", "value": "100", "block": 123},
                            cost_usd=0.01))
        ranked = lb.ranked()
        self.assertEqual(ranked[0].provider_id, "b")
        self.assertEqual(ranked[0].pass_rate, 1.0)
        self.assertEqual(ranked[1].pass_rate, 0.0)


if __name__ == "__main__":
    unittest.main()


class TestScoringV2(unittest.TestCase):
    """Scoring v2 (expansion set only, 9 Nov 2026). Mock fixtures only."""

    def _unknown(self, strict):
        return Trap("mock-unknown", "ONCHAIN_TX_LOOKUP_GENERAL",
                    "0x" + "cd" * 32, expected_status="not_found",
                    strict_unknown=strict)

    def test_frozen12_default_is_v1(self):
        # A Trap built without the flag defaults to strict_unknown=False,
        # so the frozen-12 path is untouched.
        self.assertFalse(trap().strict_unknown)

    def test_v1_unknown_ignores_invented_field(self):
        # V1 behaviour, preserved: expected-None fields are skipped, so
        # an invented `from` on a clean not_found answer does NOT fail
        # under v1. (This is the gap v2 closes — for the new set only.)
        s = score_answer(self._unknown(strict=False), "miner-1",
                         {"status": "not_found",
                          "from": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"})
        self.assertTrue(s.passed)

    def test_v2_unknown_catches_invented_field(self):
        s = score_answer(self._unknown(strict=True), "miner-1",
                         {"status": "not_found",
                          "from": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"})
        self.assertFalse(s.passed)
        invented = [f for f in s.fields if f.field == "from"]
        self.assertEqual(len(invented), 1)
        self.assertFalse(invented[0].passed)
        self.assertEqual(invented[0].expected, "(absent)")

    def test_v2_unknown_catches_invented_value_and_block(self):
        s = score_answer(self._unknown(strict=True), "miner-1",
                         {"status": "not_found", "value": "100",
                          "block": 123})
        self.assertFalse(s.passed)
        self.assertEqual(sorted(f.field for f in s.fields
                                if not f.passed),
                         ["block", "value"])

    def test_v2_unknown_clean_not_found_passes(self):
        s = score_answer(self._unknown(strict=True), "miner-1",
                         {"status": "not_found"})
        self.assertTrue(s.passed)
        self.assertEqual([f.field for f in s.fields], ["status"])

    def test_v2_token_trap_passable_on_native_value_zero(self):
        # Expansion token traps score the NATIVE tx value (0 wei here),
        # not the Transfer-event amount — so a spec-correct provider
        # returning value 0 passes in principle (frozen t03/t04, scored
        # on the event amount, were unwinnable in practice).
        from traptest.normalise import normalise
        tok = Trap("mock-token-v2", "ONCHAIN_TX_LOOKUP_GENERAL",
                   "0x" + "ef" * 32, expected_status="confirmed",
                   expected_from="0xAAA", expected_to="0xBBB",
                   expected_value="0", expected_block=123)
        norm, _ = normalise({"status": "confirmed", "from": "0xaaa",
                             "to": "0xBBB", "value_eth": 0, "block": 123})
        s = score_answer(tok, "miner-1", norm)
        self.assertTrue(s.passed)

    def test_field_accuracy_counts_fields_not_traps(self):
        from traptest.scoring import field_accuracy
        good = score_answer(trap(), "miner-1",
                            {"status": "confirmed", "from": "0xaaa",
                             "to": "0xBBB", "value": "100", "block": 123})
        bad = score_answer(trap(), "miner-1",
                           {"status": "confirmed", "from": "0xaaa"})
        correct, scored = field_accuracy([good, bad])
        # good: 5/5; bad: status+from pass, to/value/block fail = 2/5.
        self.assertEqual((correct, scored), (7, 10))

    def test_leaderboard_tracks_field_accuracy(self):
        lb = Leaderboard()
        lb.add(score_answer(trap(), "b",
                            {"status": "confirmed", "from": "0xaaa",
                             "to": "0xBBB", "value": "100", "block": 123},
                            cost_usd=0.02))
        lb.add(score_answer(trap(), "b",
                            {"status": "confirmed", "from": "0xaaa"},
                            cost_usd=0.01))
        ranked = lb.ranked()
        self.assertEqual(ranked[0].fields_correct, 7)
        self.assertEqual(ranked[0].fields_scored, 10)
        self.assertAlmostEqual(ranked[0].field_accuracy, 0.7)
