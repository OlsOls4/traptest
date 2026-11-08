"""Tests for Trap validation and freeze_traps.mk() — MOCK fixtures only.

No real transaction hashes, no network: mk() is exercised with
fabricated tx/receipt dicts in the shape the freeze script builds.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.traps import Trap
from scripts.freeze_traps import mk

MOCK_HASH = "0x" + "ab" * 32


class TestTrapHashValidation(unittest.TestCase):
    def test_non_hex_hash_rejected(self):
        with self.assertRaises(ValueError):
            Trap("mock-1", "ONCHAIN_TX_LOOKUP_GENERAL", "0x" + "zz" * 32,
                 expected_status="confirmed")
        with self.assertRaises(ValueError):
            Trap("mock-1", "ONCHAIN_TX_LOOKUP_GENERAL",
                 "0x" + "ab" * 31 + "zz",
                 expected_status="confirmed")

    def test_valid_hex_hash_accepted(self):
        t = Trap("mock-1", "ONCHAIN_TX_LOOKUP_GENERAL", MOCK_HASH,
                 expected_status="confirmed")
        self.assertEqual(t.tx_hash, MOCK_HASH)

    def test_short_or_unprefixed_hash_rejected(self):
        with self.assertRaises(ValueError):
            Trap("mock-1", "ONCHAIN_TX_LOOKUP_GENERAL", "ab" * 32,
                 expected_status="confirmed")
        with self.assertRaises(ValueError):
            Trap("mock-1", "ONCHAIN_TX_LOOKUP_GENERAL", "0x" + "ab" * 16,
                 expected_status="confirmed")


class TestFreezeMk(unittest.TestCase):
    def _tx_receipt(self, value_hex="0x0", status="0x1", block="0x3039"):
        tx = {"hash": MOCK_HASH, "from": "0xAAA", "to": "0xBBB",
              "value": value_hex}
        rec = {"status": status, "blockNumber": block}
        return tx, rec

    def test_mk_confirmed_with_value(self):
        tx, rec = self._tx_receipt(value_hex="0x64")
        tr = mk(tx, rec, "plain_transfer", "t", "2026-11-06T13:59:42Z")
        self.assertEqual(tr["expected_status"], "confirmed")
        self.assertEqual(tr["expected_value"], "100")
        self.assertEqual(tr["expected_block"], 12345)
        self.assertEqual(tr["tx_hash"], MOCK_HASH)

    def test_mk_zero_value_is_unscored(self):
        tx, rec = self._tx_receipt(value_hex="0x0")
        tr = mk(tx, rec, "plain_transfer", "t", "2026-11-06T13:59:42Z")
        self.assertIsNone(tr["expected_value"])
        self.assertIsNone(tr["value_basis"])

    def test_mk_reverted(self):
        tx, rec = self._tx_receipt(status="0x0")
        tr = mk(tx, rec, "reverted_tx", "t", "2026-11-06T13:59:42Z")
        self.assertEqual(tr["expected_status"], "reverted")


if __name__ == "__main__":
    unittest.main()
