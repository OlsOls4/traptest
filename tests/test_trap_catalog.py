"""Tests for trap_catalog — MOCK fixtures only, NOT event evidence.

No real transaction hashes, no live purchases, no miner IDs appear
here. The hashes below are made-up hex strings used to exercise the
validation logic of the framework.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.traps import Trap
from traptest.trap_catalog import (
    CATEGORY_SPECS,
    RECOMMENDED_COMPOSITION,
    GroundTruthProvenance,
    build_fixed_set,
    estimate_cost,
    validate_provenance,
)

MOCK_HASH = "0x" + "cd" * 32
MOCK_HASH_2 = "0x" + "ef" * 32
SOURCE = "https://sepolia.basescan.org/tx/0xmock"


def plain_trap():
    return Trap("mock-plain", "ONCHAIN_TX_LOOKUP", MOCK_HASH,
                expected_status="confirmed", expected_from="0xAAA",
                expected_to="0xBBB", expected_value="1000",
                expected_block=12345)


def plain_prov():
    return GroundTruthProvenance(
        trap_id="mock-plain", category="plain_transfer",
        source_name="Mock Explorer", source_url=SOURCE,
        tx_reference=MOCK_HASH, block_reference=12345,
        checked_at="2026-11-03", checker="mock-checker",
        notes="value basis: tx value field, raw wei")


def reverted_trap():
    return Trap("mock-reverted", "ONCHAIN_TX_LOOKUP", MOCK_HASH_2,
                expected_status="reverted", expected_from="0xAAA",
                expected_to="0xBBB", expected_block=12346)


def reverted_prov():
    return GroundTruthProvenance(
        trap_id="mock-reverted", category="reverted_tx",
        source_name="Mock Explorer", source_url=SOURCE,
        tx_reference=MOCK_HASH_2, block_reference=12346,
        checked_at="2026-11-03", checker="mock-checker")


def unknown_trap():
    return Trap("mock-unknown", "ONCHAIN_TX_LOOKUP", "0x" + "12" * 32,
                expected_status="not_found")


def unknown_prov():
    return GroundTruthProvenance(
        trap_id="mock-unknown", category="unknown_tx",
        source_name="Mock Explorer",
        source_url="https://sepolia.basescan.org/tx/0xmock-search",
        tx_reference="0x" + "12" * 32, block_reference=None,
        checked_at="2026-11-03", checker="mock-checker",
        notes="explorer search returned no record at freeze time")


class TestProvenance(unittest.TestCase):
    def test_valid_provenance_passes(self):
        validate_provenance(plain_prov(), plain_trap())

    def test_tx_reference_mismatch_rejected(self):
        prov = GroundTruthProvenance(
            trap_id="mock-plain", category="plain_transfer",
            source_name="Mock Explorer", source_url=SOURCE,
            tx_reference=MOCK_HASH_2, block_reference=12345,
            checked_at="2026-11-03", checker="mock-checker")
        with self.assertRaises(ValueError):
            validate_provenance(prov, plain_trap())

    def test_block_reference_mismatch_rejected(self):
        prov = GroundTruthProvenance(
            trap_id="mock-plain", category="plain_transfer",
            source_name="Mock Explorer", source_url=SOURCE,
            tx_reference=MOCK_HASH, block_reference=99999,
            checked_at="2026-11-03", checker="mock-checker")
        with self.assertRaises(ValueError):
            validate_provenance(prov, plain_trap())

    def test_non_http_source_rejected(self):
        prov = GroundTruthProvenance(
            trap_id="mock-plain", category="plain_transfer",
            source_name="Mock Explorer", source_url="not-a-url",
            tx_reference=MOCK_HASH, block_reference=12345,
            checked_at="2026-11-03", checker="mock-checker")
        with self.assertRaises(ValueError):
            validate_provenance(prov, plain_trap())

    def test_missing_required_field_rejected(self):
        trap = Trap("mock-plain", "ONCHAIN_TX_LOOKUP", MOCK_HASH,
                    expected_status="confirmed", expected_from="0xAAA",
                    expected_to="0xBBB", expected_block=12345)  # no value
        with self.assertRaises(ValueError):
            validate_provenance(plain_prov(), trap)

    def test_unknown_tx_with_extra_field_rejected(self):
        trap = Trap("mock-unknown", "ONCHAIN_TX_LOOKUP", "0x" + "12" * 32,
                    expected_status="not_found", expected_from="0xAAA")
        with self.assertRaises(ValueError):
            validate_provenance(unknown_prov(), trap)

    def test_wrong_status_for_category_rejected(self):
        trap = Trap("mock-reverted", "ONCHAIN_TX_LOOKUP", MOCK_HASH_2,
                    expected_status="confirmed", expected_from="0xAAA",
                    expected_to="0xBBB", expected_block=12346)
        with self.assertRaises(ValueError):
            validate_provenance(reverted_prov(), trap)

    def test_pending_never_a_trap(self):
        trap = Trap("mock-pending", "ONCHAIN_TX_LOOKUP", MOCK_HASH,
                    expected_status="pending")
        prov = GroundTruthProvenance(
            trap_id="mock-pending", category="plain_transfer",
            source_name="Mock Explorer", source_url=SOURCE,
            tx_reference=MOCK_HASH, block_reference=None,
            checked_at="2026-11-03", checker="mock-checker")
        with self.assertRaises(ValueError):
            validate_provenance(prov, trap)


class TestFixedSet(unittest.TestCase):
    def test_minimal_valid_set_passes(self):
        traps = build_fixed_set([
            (reverted_trap(), reverted_prov()),
            (unknown_trap(), unknown_prov()),
        ])
        self.assertEqual(len(traps), 2)

    def test_missing_mandatory_category_rejected(self):
        with self.assertRaises(ValueError):
            build_fixed_set([(plain_trap(), plain_prov())])

    def test_over_cap_rejected(self):
        entries = []
        for i in range(15):
            t = Trap(f"mock-r{i}", "ONCHAIN_TX_LOOKUP",
                     "0x" + f"{i:02x}" * 32, expected_status="reverted",
                     expected_from="0xAAA", expected_to="0xBBB",
                     expected_block=100 + i)
            p = GroundTruthProvenance(
                trap_id=f"mock-r{i}", category="reverted_tx",
                source_name="Mock Explorer", source_url=SOURCE,
                tx_reference="0x" + f"{i:02x}" * 32,
                block_reference=100 + i, checked_at="2026-11-03",
                checker="mock-checker")
            entries.append((t, p))
        entries.append((unknown_trap(), unknown_prov()))
        # 15 reverted + 1 unknown = 16, under cap. Add 15 plain traps
        # to push the set to 31, over the cap.
        for i in range(15, 30):
            t = Trap(f"mock-p{i}", "ONCHAIN_TX_LOOKUP",
                     "0x" + f"{i:02x}" * 32, expected_status="confirmed",
                     expected_from="0xAAA", expected_to="0xBBB",
                     expected_value="1", expected_block=200 + i)
            p = GroundTruthProvenance(
                trap_id=f"mock-p{i}", category="plain_transfer",
                source_name="Mock Explorer", source_url=SOURCE,
                tx_reference="0x" + f"{i:02x}" * 32,
                block_reference=200 + i, checked_at="2026-11-03",
                checker="mock-checker")
            entries.append((t, p))
        self.assertEqual(len(entries), 31)
        with self.assertRaises(ValueError):
            build_fixed_set(entries)


class TestCostAndComposition(unittest.TestCase):
    def test_recommended_set_cost(self):
        cost = estimate_cost(12, 2)
        self.assertEqual(cost["calls"], 24)
        self.assertEqual(cost["base_usd"], 0.24)
        self.assertAlmostEqual(cost["total_usd"], 0.2448)

    def test_cap_cost(self):
        cost = estimate_cost(30, 2)
        self.assertEqual(cost["calls"], 60)
        self.assertAlmostEqual(cost["total_usd"], 0.612)

    def test_recommended_composition_sums_to_twelve(self):
        self.assertEqual(sum(RECOMMENDED_COMPOSITION.values()), 12)
        for cat in RECOMMENDED_COMPOSITION:
            self.assertIn(cat, CATEGORY_SPECS)

    def test_every_category_has_required_status_and_fields(self):
        for cat, spec in CATEGORY_SPECS.items():
            self.assertIn(spec["required_status"],
                          ("confirmed", "reverted", "not_found"))
            self.assertIn("status", spec["required_fields"])
            self.assertTrue(spec["ground_truth_source"])
            self.assertTrue(spec["value_basis"])


if __name__ == "__main__":
    unittest.main()
