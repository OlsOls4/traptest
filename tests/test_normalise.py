"""Tests for the shared normaliser (traptest/normalise.py) and the
canonical numeric scorer (traptest/scoring.py) — MOCK fixtures only.

These tests FAIL on the pre-fix code for the hex, "100.0", scientific
notation and integer-ETH cases (verified 8 Nov 2026 by running the
same cases against the old normalise()/_norm verbatim: old code
passed "1e-05" and "0x64" through unchanged, treated integer ETH as
wei, and string-compared "100.0" != "100").
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.normalise import normalise
from traptest.scoring import score_answer
from traptest.traps import Trap

MOCK_HASH = "0x" + "ab" * 32


def trap(value="100", block=123):
    return Trap("mock-1", "ONCHAIN_TX_LOOKUP_GENERAL", MOCK_HASH,
                expected_status="confirmed",
                expected_from="0xAAA", expected_to="0xBBB",
                expected_value=value, expected_block=block)


class TestNormalise(unittest.TestCase):
    def test_decimal_eth_to_wei(self):
        out, notes = normalise({"value_eth": 0.001, "block_number": 123})
        self.assertEqual(out["value"], "1000000000000000")
        self.assertEqual(out["block"], 123)

    def test_scientific_notation_eth(self):
        # Truvian t08: value_eth 1e-05 == 10000000000000 wei. The old
        # code only converted strings containing "." and passed
        # "1e-05" through, scoring a correct answer FAIL.
        out, _ = normalise({"value_eth": 1e-05})
        self.assertEqual(out["value"], "10000000000000")
        out, _ = normalise({"value_eth": "1e-05"})
        self.assertEqual(out["value"], "10000000000000")

    def test_integer_eth_is_eth_not_wei(self):
        out, _ = normalise({"value_eth": 1})
        self.assertEqual(out["value"], "1000000000000000000")
        out, _ = normalise({"value_eth": 0})
        self.assertEqual(out["value"], "0")

    def test_hex_value_eth_is_wei(self):
        out, _ = normalise({"value_eth": "0x64"})
        self.assertEqual(out["value"], "100")

    def test_block_number_vs_block(self):
        out, notes = normalise({"block_number": 53047427})
        self.assertEqual(out["block"], 53047427)
        self.assertIn("block_number -> block", notes)
        # An existing block is never overwritten by block_number.
        out, _ = normalise({"block": 1, "block_number": 2})
        self.assertEqual(out["block"], 1)
        # Hex block canonicalises to int.
        out, _ = normalise({"block_number": "0x7b"})
        self.assertEqual(out["block"], 123)

    def test_missing_keys(self):
        out, notes = normalise({})
        self.assertEqual(out, {})
        self.assertEqual(notes, [])
        out, notes = normalise(None)
        self.assertEqual(out, {})
        out, _ = normalise({"status": "confirmed", "value_eth": None})
        self.assertNotIn("value", out)
        out, _ = normalise({"status": "confirmed", "block_number": None})
        self.assertNotIn("block", out)

    def test_existing_value_canonicalised(self):
        out, _ = normalise({"value": "100.0"})
        self.assertEqual(out["value"], "100")
        out, _ = normalise({"value": "0x64"})
        self.assertEqual(out["value"], "100")

    def test_input_not_mutated(self):
        raw = {"value_eth": 0.001, "block_number": 5}
        normalise(raw)
        self.assertEqual(raw, {"value_eth": 0.001, "block_number": 5})


class TestScoringNumerics(unittest.TestCase):
    def test_value_100_point_0_equals_100(self):
        s = score_answer(trap(), "miner-1",
                         {"status": "confirmed", "from": "0xaaa",
                          "to": "0xBBB", "value": "100.0", "block": 123})
        self.assertTrue(s.passed)

    def test_value_hex_equals_decimal(self):
        s = score_answer(trap(), "miner-1",
                         {"status": "confirmed", "from": "0xaaa",
                          "to": "0xBBB", "value": "0x64", "block": 123})
        self.assertTrue(s.passed)

    def test_value_scientific_equals_decimal(self):
        # "1e-05" as a wei value is 0.00001 wei — not equal to 100;
        # the point is the comparison is numeric, not string-based.
        s = score_answer(trap(value="10000000000000"), "miner-1",
                         {"status": "confirmed", "from": "0xaaa",
                          "to": "0xBBB", "value": "1e13", "block": 123})
        self.assertTrue(s.passed)

    def test_block_hex_equals_decimal(self):
        s = score_answer(trap(), "miner-1",
                         {"status": "confirmed", "from": "0xaaa",
                          "to": "0xBBB", "value": "100", "block": "0x7b"})
        self.assertTrue(s.passed)

    def test_block_string_equals_int(self):
        s = score_answer(trap(), "miner-1",
                         {"status": "confirmed", "from": "0xaaa",
                          "to": "0xBBB", "value": "100", "block": "123"})
        self.assertTrue(s.passed)

    def test_value_still_fails_when_numerically_different(self):
        s = score_answer(trap(), "miner-1",
                         {"status": "confirmed", "from": "0xaaa",
                          "to": "0xBBB", "value": "101", "block": 123})
        self.assertFalse(s.passed)

    def test_full_pipeline_t08_shape(self):
        # End to end on the Truvian t08 shape: raw answer with
        # value_eth 1e-05 against expected 10000000000000 wei.
        raw = {"status": "reverted", "from": "0xAAA", "to": "0xBBB",
               "block_number": 55258555, "value_eth": 1e-05}
        norm, _ = normalise(raw)
        s = score_answer(
            Trap("t08-reverted-tx", "ONCHAIN_TX_LOOKUP_GENERAL", MOCK_HASH,
                 expected_status="reverted", expected_from="0xAAA",
                 expected_to="0xBBB",
                 expected_value="10000000000000", expected_block=55258555),
            "8453", norm)
        self.assertTrue(s.passed)


if __name__ == "__main__":
    unittest.main()
