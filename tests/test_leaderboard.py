"""Tests for the leaderboard unservable tier — MOCK fixtures only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.leaderboard import Leaderboard
from traptest.scoring import score_answer
from traptest.traps import Trap

MOCK_HASH = "0x" + "ab" * 32


def trap():
    return Trap("mock-1", "ONCHAIN_TX_LOOKUP_GENERAL", MOCK_HASH,
                expected_status="confirmed",
                expected_from="0xAAA", expected_to="0xBBB",
                expected_value="100", expected_block=123)


def good(provider):
    return score_answer(trap(), provider,
                        {"status": "confirmed", "from": "0xaaa",
                         "to": "0xBBB", "value": "100", "block": 123},
                        cost_usd=0.01)


def bad(provider):
    return score_answer(trap(), provider,
                        {"status": "reverted", "from": "0xaaa",
                         "to": "0xBBB", "value": "100", "block": 123},
                        cost_usd=0.01)


class TestUnservableTier(unittest.TestCase):
    def test_unservable_never_ranked(self):
        lb = Leaderboard()
        lb.add(good("8453"))
        lb.add(bad("9002"))
        lb.mark_unservable("4433")
        lb.mark_unservable("9010")
        lb.mark_unservable("900")
        ranked = lb.ranked()
        self.assertEqual([s.provider_id for s in ranked], ["8453", "9002"])
        self.assertEqual(lb.unservable_providers(), ["4433", "900", "9010"])

    def test_served_provider_at_zero_percent_still_ranked(self):
        # Failing every answered trap is evidence and ranks at 0%;
        # serving nothing is not a pass rate at all.
        lb = Leaderboard()
        lb.add(bad("9002"))
        lb.mark_unservable("4433")
        ranked = lb.ranked()
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].provider_id, "9002")
        self.assertEqual(ranked[0].pass_rate, 0.0)

    def test_add_served_false_marks_unservable(self):
        lb = Leaderboard()
        lb.add(good("8453"), served=False)
        self.assertEqual(lb.ranked(), [])
        self.assertEqual(lb.unservable_providers(), ["8453"])

    def test_provider_serving_later_leaves_unservable_tier(self):
        lb = Leaderboard()
        lb.mark_unservable("8453")
        lb.add(good("8453"))
        self.assertEqual(lb.unservable_providers(), [])
        self.assertEqual([s.provider_id for s in lb.ranked()], ["8453"])


if __name__ == "__main__":
    unittest.main()
