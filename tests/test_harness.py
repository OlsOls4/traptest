"""Tests for the shared harness (traptest/harness.py) — F3 provenance
enforcement, F7 structural escrow parsing, F8 atomic writes.

No network, no spend, ever. The live-data test reads the FROZEN
results file read-only; it never writes to results-live/.
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import traptest.harness as harness
from traptest.harness import (
    atomic_write_text, build_scored_row, fail_row, load_traps,
    verify_receipts)
from traptest.receipts import (
    SETTLEMENT_PAY_TO, SETTLEMENT_TOKEN, TRANSFER_TOPIC)
from traptest.traps import Trap

ROOT = Path(__file__).resolve().parent.parent
FROZEN_TRAPS = ROOT / "traps-frozen-2026-11-06.json"
FROZEN_RESULTS = ROOT / "results-live" / "full-run-2026-11-06.json"
INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
MOCK_HASH = "0x" + "ab" * 32


def _trap(trap_id="t01-mock", **kw):
    kw.setdefault("intent", INTENT)
    kw.setdefault("tx_hash", MOCK_HASH)
    kw.setdefault("expected_status", "confirmed")
    return Trap(trap_id, **kw)


# --- F7: structural escrow parsing ---------------------------------------

# The exact truncated error string from a live Sigil (9010) row: the
# 300-char cut lands inside the payment message, AFTER the status.
ESCROW_TRUNCATED = (
    'PurchaseFailedError: Ask failed (status 500): '
    '{"error":"upstream error 404: Not Found\\n",'
    '"intent":"ONCHAIN_TX_LOOKUP_GENERAL","miner_id":"9010",'
    '"payment":{"status":"escrow_credit_pending","message":"Your '
    'payment settled but the request failed, so nothing was billed. '
    'The amount is being credited to your Telegraph escrow ')

# A live OnChain Intel (900) error, FULL (untruncated): the nested
# upstream message is long, so the payment object sits beyond the
# 300-char cut — the old code lost this evidence entirely.
ESCROW_FULL_900 = (
    'PurchaseFailedError: Ask failed (status 500): ' + json.dumps({
        "error": 'upstream error 400: {"ok":false,"status":"error",'
                 '"intent":"ONCHAIN_TX_LOOKUP","error":"Could not '
                 'determine a supported chain.","hint":"Supported '
                 'chains: ethereum, base, polygon, bsc, arbitrum, '
                 'optimism, avalanche, scroll..."}',
        "intent": "ONCHAIN_TX_LOOKUP_GENERAL",
        "miner_id": "900",
        "payment": {"status": "escrow_credit_pending",
                    "message": "Your payment settled but the request "
                               "failed, so nothing was billed."}}))


class TestFailRowEscrow(unittest.TestCase):
    def test_truncated_live_escrow_error_credits(self):
        row = fail_row(_trap(), "9010", ESCROW_TRUNCATED)
        self.assertEqual(row.get("escrow_credit_usd"), 0.01)
        # The stored error keeps the historical truncation.
        self.assertEqual(row["error"], ESCROW_TRUNCATED)

    def test_full_900_style_error_credits_past_the_cut(self):
        row = fail_row(_trap(), "900", ESCROW_FULL_900)
        self.assertEqual(row.get("escrow_credit_usd"), 0.01)
        # Stored error is the historical format: type prefix + first
        # 300 chars of the detail (321 chars total).
        self.assertEqual(len(row["error"]), 321)
        self.assertTrue(row["error"].startswith(
            "PurchaseFailedError: Ask failed (status 500): {"))

    def test_whole_json_escrow_error_credits(self):
        row = fail_row(_trap(), "9010",
                       'PurchaseFailedError: Ask failed (status 500): '
                       '{"error":"x","payment":{"status":'
                       '"escrow_credit_pending","message":"y"}}')
        self.assertEqual(row.get("escrow_credit_usd"), 0.01)

    def test_free_text_escrow_does_not_credit(self):
        # The old bug: any error mentioning "escrow" was credited.
        row = fail_row(_trap(), "900",
                       "PurchaseFailedError: escrow service unavailable")
        self.assertNotIn("escrow_credit_usd", row)
        row = fail_row(_trap(), "900",
                       'PurchaseFailedError: Ask failed (status 500): '
                       '{"error":"escrow_credit_pending was mentioned '
                       'in a message","payment":{"status":"settled"}}')
        self.assertNotIn("escrow_credit_usd", row)

    def test_other_payment_statuses_do_not_credit(self):
        for status in ("settled", "escrow_credit_failed", "refunded",
                       "pending", ""):
            row = fail_row(_trap(), "900",
                           '{"error":"x","payment":{"status":'
                           + json.dumps(status) + '}}')
            self.assertNotIn("escrow_credit_usd", row,
                             f"status {status!r} must not credit")

    def test_non_json_and_missing_errors_do_not_credit(self):
        for error in (None, "", "plain failure, no json",
                      'PurchaseFailedError: Ask failed (status 503): '
                      '{"error":"no_compatible_miner"}'):
            row = fail_row(_trap(), "4433", error)
            self.assertNotIn("escrow_credit_usd", row)

    def test_live_rows_reproduce_old_outcome_on_stored_strings(self):
        # The 24/24 live escrow rows keep validating: on the STORED
        # (truncated) strings the new parser gives exactly the old
        # substring check's outcome (12 credits, all Sigil 9010 —
        # the OnChain Intel strings were cut before the payment
        # object, so neither parser credits them from the string;
        # their credits in the frozen file come from the post-hoc
        # balance repair, and the file itself is untouched).
        doc = json.loads(FROZEN_RESULTS.read_text())
        rows = doc["scores"]
        self.assertEqual(len(rows), 60)
        self.assertEqual(sum(1 for r in rows
                             if "escrow_credit_usd" in r), 24)
        credited = 0
        for r in rows:
            row = fail_row(_trap(r["trap_id"]), r["provider_id"],
                           r.get("error"))
            # Stored error byte-identical to the live file.
            self.assertEqual(row["error"], r.get("error"))
            old = "escrow" in (r.get("error") or "").lower()
            new = "escrow_credit_usd" in row
            self.assertEqual(new, old, (r["trap_id"], r["provider_id"]))
            credited += new
        self.assertEqual(credited, 12)


# --- F3: provenance enforcement in load_traps ----------------------------

def _prov(trap_id, category, block, tx_hash=MOCK_HASH):
    return {"source": "Mock Explorer",
            "source_url": "https://example.invalid/tx/mock",
            "block": block, "checked_at": "2026-11-03",
            "checker": "mock-checker", "notes": "mock, NOT event evidence"}


def _trap_dict(trap_id, category, status, tx_hash, block=None,
               extra=None, prov=True):
    d = {"trap_id": trap_id, "category": category, "intent": INTENT,
         "tx_hash": tx_hash, "expected_status": status,
         "expected_from": "0x" + "11" * 20,
         "expected_to": "0x" + "22" * 20,
         "expected_value": "1000" if status == "confirmed" else None,
         "expected_block": block}
    if status == "not_found":
        d.update(expected_from=None, expected_to=None,
                 expected_value=None, expected_block=None)
    if status == "reverted":
        d["expected_value"] = None
    if extra:
        d.update(extra)
    if prov:
        d["provenance"] = _prov(trap_id, category, block, tx_hash)
    return d


def _valid_pair():
    return [
        _trap_dict("mock-reverted", "reverted_tx", "reverted",
                   "0x" + "aa" * 32, block=100),
        _trap_dict("mock-unknown", "unknown_tx", "not_found",
                   "0x" + "bb" * 32),
    ]


class TestLoadTrapsProvenance(unittest.TestCase):
    def _write(self, traps):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"intent": INTENT, "traps": traps}, f)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_minimal_valid_set_loads(self):
        path = self._write(_valid_pair())
        doc, traps, sha = load_traps(path)
        self.assertEqual([t.trap_id for t in traps],
                         ["mock-reverted", "mock-unknown"])
        self.assertEqual(sha, hashlib.sha256(
            Path(path).read_bytes()).hexdigest())

    def test_frozen_file_loads_with_known_sha(self):
        doc, traps, sha = load_traps(FROZEN_TRAPS)
        self.assertEqual(len(traps), 12)
        self.assertEqual(
            sha, "0f84494bc8a6b1773aa74f2f9e3c15b6e7eb42b397c8849bbea3068bd4a1d534")

    def test_provenance_less_trap_rejected(self):
        traps = _valid_pair()
        for t in traps:
            t.pop("provenance", None)
        with self.assertRaises(ValueError) as ctx:
            load_traps(self._write(traps))
        self.assertIn("provenance", str(ctx.exception))

    def test_pending_trap_rejected(self):
        traps = _valid_pair()
        traps.append(_trap_dict("mock-pending", "plain_transfer", "pending",
                                "0x" + "cc" * 32, block=None))
        with self.assertRaises(ValueError) as ctx:
            load_traps(self._write(traps))
        self.assertIn("pending", str(ctx.exception))

    def test_missing_mandatory_category_rejected(self):
        traps = [_trap_dict("mock-plain", "plain_transfer", "confirmed",
                            "0x" + "cc" * 32, block=100)]
        with self.assertRaises(ValueError) as ctx:
            load_traps(self._write(traps))
        self.assertIn("mandatory", str(ctx.exception))

    def test_unknown_category_rejected(self):
        # Note: a tx_reference mismatch cannot be constructed through
        # the file format — load_traps takes tx_reference from the
        # trap's own tx_hash by construction — so this exercises the
        # unknown-category rejection instead.
        traps = _valid_pair()
        traps[0]["category"] = "no_such_category"
        with self.assertRaises(ValueError) as ctx:
            load_traps(self._write(traps))
        self.assertIn("unknown trap category", str(ctx.exception))

    def test_over_max_traps_rejected(self):
        traps = []
        for i in range(30):
            traps.append(_trap_dict(
                f"mock-r{i:02d}", "reverted_tx", "reverted",
                "0x" + f"{i:02x}" * 32, block=100 + i))
        traps.append(_trap_dict("mock-u", "unknown_tx", "not_found",
                                "0x" + "ff" * 32))
        self.assertEqual(len(traps), 31)
        with self.assertRaises(ValueError) as ctx:
            load_traps(self._write(traps))
        self.assertIn("over the cap", str(ctx.exception))

    def test_exactly_max_traps_loads(self):
        traps = []
        for i in range(29):
            traps.append(_trap_dict(
                f"mock-r{i:02d}", "reverted_tx", "reverted",
                "0x" + f"{i:02x}" * 32, block=100 + i))
        traps.append(_trap_dict("mock-u", "unknown_tx", "not_found",
                                "0x" + "ff" * 32))
        doc, loaded, _ = load_traps(self._write(traps))
        self.assertEqual(len(loaded), 30)


# --- F8: atomic writes ----------------------------------------------------

class TestAtomicWrite(unittest.TestCase):
    def test_write_and_overwrite_leave_no_temp_files(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "results.json"
            atomic_write_text(path, '{"a": 1}')
            self.assertEqual(path.read_text(), '{"a": 1}')
            atomic_write_text(path, '{"a": 2}')
            self.assertEqual(path.read_text(), '{"a": 2}')
            leftovers = [p for p in Path(d).iterdir()
                         if p.name != "results.json"]
            self.assertEqual(leftovers, [])


# --- Scoring version from the trap file (13 Nov 2026) ---------------------

def _fake_result(answer):
    return SimpleNamespace(answer=answer, cost_usd=0.01,
                           signal_hash="mock-sig", receipt=None,
                           charged=True)


def _answer_for(trap):
    ans = {"status": trap.expected_status}
    if trap.expected_from is not None:
        ans["from"] = trap.expected_from
    if trap.expected_to is not None:
        ans["to"] = trap.expected_to
    if trap.expected_value is not None:
        ans["value"] = trap.expected_value
    if trap.expected_block is not None:
        ans["block"] = trap.expected_block
    return ans


class TestScoringVersionFromTrapFile(unittest.TestCase):
    """Regression: build_scored_row derives scoring_version from the
    trap file's declared version. The old code stamped v1 on every
    trap without strict_unknown, so expansion traps t13-t22 would
    re-emit v1 labels (the clean run's v2 labels were fixed by file
    edit, not code)."""

    def test_expansion_non_strict_trap_stamps_v2(self):
        doc, traps, _ = load_traps(ROOT / "traps-frozen-2026-11-09.json")
        by_id = {t["trap_id"]: t for t in doc["traps"]}
        t13 = next(t for t in traps if t.trap_id == "t13-token-transfer")
        self.assertFalse(t13.strict_unknown)  # not an unknown trap
        row = build_scored_row(t13, by_id["t13-token-transfer"],
                               "9002", INTENT, _fake_result(_answer_for(t13)))
        self.assertEqual(row["scoring_version"], "v2-strict-unknown")

    def test_expansion_unknown_trap_stamps_v2(self):
        doc, traps, _ = load_traps(ROOT / "traps-frozen-2026-11-09.json")
        by_id = {t["trap_id"]: t for t in doc["traps"]}
        t23 = next(t for t in traps if t.trap_id == "t23-unknown-tx")
        self.assertTrue(t23.strict_unknown)
        row = build_scored_row(t23, by_id["t23-unknown-tx"],
                               "9002", INTENT, _fake_result(_answer_for(t23)))
        self.assertEqual(row["scoring_version"], "v2-strict-unknown")

    def test_frozen12_trap_stamps_v1(self):
        doc, traps, _ = load_traps(FROZEN_TRAPS)
        by_id = {t["trap_id"]: t for t in doc["traps"]}
        t01 = traps[0]
        self.assertIsNone(t01.scoring_version)  # file declares none
        row = build_scored_row(t01, by_id[t01.trap_id],
                               "9002", INTENT, _fake_result(_answer_for(t01)))
        self.assertEqual(row["scoring_version"], "v1")


# --- Receipt verification totals (13 Nov 2026) ----------------------------

def _transfer_log(to=SETTLEMENT_PAY_TO, amount=10000,
                  token=SETTLEMENT_TOKEN):
    return {
        "address": token,
        "topics": [TRANSFER_TOPIC,
                   "0x" + "00" * 12 + "170dfa67d1e37915d8130eab9bd3b0a4e115f0c0",
                   "0x" + "00" * 12 + to[2:].lower()],
        "data": "0x" + format(amount, "064x"),
    }


def _settled_receipt():
    return {"status": "0x1", "logs": [_transfer_log()],
            "transactionHash": "0x" + "aa" * 32}


class TestVerifyReceiptsTotals(unittest.TestCase):
    """Undecodable receipts count as FAILED in verify totals — never
    silently excluded. Rows with no receipt at all are not counted
    (they are fail rows, not served receipts)."""

    def test_undecodable_receipt_counts_as_failed(self):
        rows = [{"trap_id": "t01", "provider_id": "9002",
                 "receipt": "!!!not-base64!!!", "receipt_present": True}]
        self.assertEqual(verify_receipts(rows), (0, 1))
        self.assertIs(rows[0]["receipt_verified_onchain"], False)

    def test_no_receipt_rows_not_counted(self):
        rows = [{"trap_id": "t01", "provider_id": "9002",
                 "receipt": None, "receipt_present": False}]
        self.assertEqual(verify_receipts(rows), (0, 0))

    def test_transient_null_results_retried_then_verified(self):
        import base64
        tx = "0x" + "ab" * 32
        receipt = base64.b64encode(
            json.dumps({"tx_hash": tx}).encode()).decode()
        rows = [{"trap_id": "t01", "provider_id": "9002",
                 "receipt": receipt, "receipt_present": True}]
        calls = {"n": 0}

        def fake_run(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                body = json.dumps([{"jsonrpc": "2.0", "id": 0,
                                    "result": None}])
            else:
                body = json.dumps([{"jsonrpc": "2.0", "id": 0,
                                    "result": _settled_receipt()}])
            return SimpleNamespace(stdout=body)

        with mock.patch.object(harness.subprocess, "run", fake_run):
            self.assertEqual(verify_receipts(rows), (1, 1))
        self.assertEqual(calls["n"], 2)
        self.assertTrue(rows[0]["receipt_verified_onchain"])
        self.assertEqual(rows[0]["receipt_settlement_tx"], tx)

    def test_persistent_null_counts_as_failed_not_excluded(self):
        import base64
        tx = "0x" + "ab" * 32
        receipt = base64.b64encode(
            json.dumps({"tx_hash": tx}).encode()).decode()
        rows = [{"trap_id": "t01", "provider_id": "9002",
                 "receipt": receipt, "receipt_present": True}]
        calls = {"n": 0}

        def fake_run(*args, **kwargs):
            calls["n"] += 1
            return SimpleNamespace(stdout=json.dumps(
                [{"jsonrpc": "2.0", "id": 0, "result": None}]))

        with mock.patch.object(harness.subprocess, "run", fake_run):
            self.assertEqual(verify_receipts(rows, max_attempts=2), (0, 1))
        self.assertEqual(calls["n"], 2)  # retried, then gave up as FAILED
        self.assertIs(rows[0]["receipt_verified_onchain"], False)


if __name__ == "__main__":
    unittest.main()
