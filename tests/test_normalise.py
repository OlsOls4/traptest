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


class TestFractionalWei(unittest.TestCase):
    """F9: a value_eth below 1 wei must never truncate to "0" — that
    would false-pass a zero-value trap."""

    def test_fractional_wei_kept_as_is(self):
        out, notes = normalise({"value_eth": "1e-19"})
        self.assertEqual(out["value"], "1e-19")
        self.assertTrue(any("fractional wei" in n for n in notes))
        out, _ = normalise({"value_eth": 1e-19})
        self.assertEqual(out["value"], "1e-19")
        out, _ = normalise({"value_eth": "5e-19"})  # 0.5 wei
        self.assertEqual(out["value"], "5e-19")

    def test_one_wei_boundary_converts(self):
        out, _ = normalise({"value_eth": "1e-18"})
        self.assertEqual(out["value"], "1")
        out, _ = normalise({"value_eth": "0.000000000000000001"})
        self.assertEqual(out["value"], "1")

    def test_fractional_wei_does_not_false_pass_zero_trap(self):
        # Expected value "0"; a 1e-19 ETH answer is NOT zero.
        raw = {"status": "confirmed", "from": "0xAAA", "to": "0xBBB",
               "value_eth": "1e-19", "block": 123}
        norm, _ = normalise(raw)
        s = score_answer(trap(value="0"), "miner-1", norm)
        self.assertFalse(s.passed)


class TestParseDecimalShared(unittest.TestCase):
    """F10: scoring.py and normalise.py share ONE _parse_decimal —
    the canonical implementation in normalise.py. Identical behaviour
    on the edge cases, proved against both import paths."""

    def test_same_function_object(self):
        import traptest.normalise as normalise_mod
        import traptest.scoring as scoring_mod
        self.assertIs(scoring_mod._parse_decimal,
                      normalise_mod._parse_decimal)

    def test_edge_cases_identical(self):
        from decimal import Decimal

        from traptest.normalise import _parse_decimal as parse_n
        from traptest.scoring import _parse_decimal as parse_s
        cases = [
            # (input, expected Decimal or None)
            (None, None), (True, None), (False, None),
            (0, Decimal(0)), (1, Decimal(1)), (-3, Decimal(-3)),
            (2.5, Decimal("2.5")), (1e-05, Decimal("1e-05")),
            ("1e-05", Decimal("1e-05")), ("0x64", Decimal(100)),
            ("0X10", Decimal(16)), ("100.0", Decimal("100.0")),
            ("  42  ", Decimal(42)), ("", None), ("   ", None),
            ("abc", None), ("0xzz", None), ("0x", None),
            ("1e100", Decimal("1e100")),
            ("123456789012345678901234567890",
             Decimal("123456789012345678901234567890")),
            ("0x" + "f" * 40, Decimal(int("f" * 40, 16))),
            (Decimal("7.5"), Decimal("7.5")),
            ("  0x2a  ", Decimal(42)),
            ("-0.5", Decimal("-0.5")),
        ]
        for value, expected in cases:
            with self.subTest(value=repr(value)):
                got_n, got_s = parse_n(value), parse_s(value)
                self.assertEqual(got_n, got_s)
                self.assertEqual(got_n, expected)
        # NaN parses (Decimal accepts it) but is never equal to
        # anything — both paths agree.
        self.assertTrue(parse_n(float("nan")).is_nan())
        self.assertTrue(parse_s(float("nan")).is_nan())


if __name__ == "__main__":
    unittest.main()
