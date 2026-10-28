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
    return Trap("mock-1", "ONCHAIN_TX_LOOKUP",
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
