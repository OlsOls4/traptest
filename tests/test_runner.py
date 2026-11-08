"""Tests for the parametrised runner (traptest/run.py) — no network,
no spend, ever. Every HTTP interaction is a fake transport; the only
key used is a fresh throwaway created in-test and never persisted.

These tests FAIL on the old code: the old run.py took no --providers /
--out (argparse rejects them) and returned 3 with "payment provider
not configured in prep" for any --traps + --miner run, and the old
scripts read .burner3.key with a bare .read_text() (unhandled
FileNotFoundError on a fresh clone) and overwrote the frozen results
file unconditionally. Verified against the pre-rebuild code before
these tests were written.
"""
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from eth_account import Account

from traptest.leaderboard import Leaderboard
from traptest.providers import (
    DirectAskClient, TransportHTTPError, _HttpResponse)  # noqa: F401  (client is exercised via run.main)
from traptest.run import main
from traptest.scoring import score_answer
from traptest.traps import Trap

INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
TODAY = date(2026, 11, 6)
PAY_TO = "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"
ASSET = "0xcc194e1a843B658526D0D5C431f670028582Ae17"

T01 = {
    "trap_id": "t01-plain-transfer",
    "category": "plain_transfer",
    "intent": INTENT,
    "tx_hash": "0x" + "11" * 32,
    "expected_status": "confirmed",
    "expected_from": "0x" + "11" * 20,
    "expected_to": "0x" + "22" * 20,
    "expected_value": "1000000000000000",
    "expected_block": 123,
}
T02 = {
    "trap_id": "t02-plain-transfer",
    "category": "plain_transfer",
    "intent": INTENT,
    "tx_hash": "0x" + "22" * 32,
    "expected_status": "confirmed",
    "expected_from": "0x" + "33" * 20,
    "expected_to": "0x" + "44" * 20,
    "expected_value": "0",
    "expected_block": 456,
}


def _json_body(obj):
    return json.dumps(obj).encode("utf-8")


class FakeTransport:
    """Fake Telegraph engine: fresh catalogue + 402-then-serve asks.

    Asks without a payment header get a 402 with the live challenge
    shape (body fallback: $0.01, Sepolia, accepted asset); asks with
    a payment header get a served answer. Provider 8453 answers
    t02 wrong on purpose (status not_found) so the leaderboard
    ranking in the end-to-end test is non-trivial.
    """

    def __init__(self):
        self.calls = []

    def __call__(self, method, url, body, headers):
        self.calls.append((method, url, dict(headers or {}), body))
        if method == "GET" and url.endswith(f"/intents/{INTENT}/miners"):
            return _HttpResponse(200, _json_body({"miners": [
                {"id": "9002", "name": "TxLens", "cost_per_call": "0.00"},
                {"id": "8453", "name": "Truvian", "cost_per_call": "0.00"},
            ]}), {"Content-Type": "application/json"})
        if method == "POST" and "/v1/ask/" in url:
            miner = url.rsplit("/ask/", 1)[1]
            paid = any(k.lower() in ("x-payment", "payment-signature")
                       for k in (headers or {}))
            if not paid:
                raise TransportHTTPError(402, _json_body(
                    {"amount_usd": 0.01, "payTo": PAY_TO,
                     "asset": ASSET, "network": "eip155:11155111"}), {})
            params = json.loads(body.decode("utf-8"))["params"]
            tx = params["tx_hash"]
            trap = T01 if tx == T01["tx_hash"] else T02
            if miner == "8453" and tx == T02["tx_hash"]:
                answer = {"status": "not_found",
                          "from": trap["expected_from"],
                          "to": trap["expected_to"],
                          "value": "0", "block": 456}
            elif tx == T01["tx_hash"]:
                # Deliberately un-normalised spellings: the runner must
                # normalise value_eth / block_number before scoring.
                answer = {"status": "confirmed",
                          "from": trap["expected_from"],
                          "to": trap["expected_to"],
                          "value_eth": "0.001", "block_number": 123}
            else:
                answer = {"status": "confirmed",
                          "from": trap["expected_from"],
                          "to": trap["expected_to"],
                          "value": "0", "block": 456}
            return _HttpResponse(200, _json_body(
                {"answer": answer, "cost_usd": 0.01,
                 "signal_hash": "mock-sig-" + miner}),
                {"Content-Type": "application/json",
                 "X-TELEGRAPH-RECEIPT": "mock-receipt-" + miner})
        raise AssertionError(f"unexpected call {method} {url}")

    @property
    def posts(self):
        return [c for c in self.calls if c[0] == "POST"]

    @property
    def gets(self):
        return [c for c in self.calls if c[0] == "GET"]


def _stub_balances(addr):
    return 30.0, 0.05


def _stub_receipts(rows):
    return 0, 0


class RunnerTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.marker = self.dir / "LIVE-ACTIVATED"
        self.marker.write_text("activated")
        # Fresh throwaway key, in-test only, never persisted elsewhere.
        self.key = self.dir / "burner.key"
        self.key.write_text("0x" + Account.create().key.hex())
        self.traps_path = self.dir / "traps.json"
        self.traps_path.write_text(json.dumps({
            "data_kind": "TRAPS", "freeze_time_utc": "2026-11-06T00:00:00Z",
            "intent": INTENT, "traps": [T01, T02]}, indent=2))
        self.traps_sha256 = hashlib.sha256(
            self.traps_path.read_bytes()).hexdigest()
        self.out = self.dir / "results" / "replay.json"
        self.out.parent.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _args(self, extra=None):
        args = ["--marker", str(self.marker),
                "--traps", str(self.traps_path),
                "--providers", "9002,8453",
                "--key", str(self.key),
                "--out", str(self.out)]
        return args + (extra or [])

    def _run(self, extra=None, transport=None, **kwargs):
        transport = transport if transport is not None else FakeTransport()
        code = main(self._args(extra), today=TODAY, transport=transport,
                    balance_reader=_stub_balances,
                    receipt_verifier=_stub_receipts, **kwargs)
        return code, transport


class TestRunnerEndToEnd(RunnerTestBase):
    """(a) freeze -> buy (fake transport, no network, no spend) ->
    score -> leaderboard, using the new runner."""

    def test_freeze_buy_score_leaderboard(self):
        code, t = self._run()
        self.assertEqual(code, 0)
        # Buys happened only via the fake transport: 4 buys x 2 POSTs
        # (402 challenge, then paid retry).
        self.assertEqual(len(t.posts), 8)
        paid = [c for c in t.posts
                if any(k.lower() in ("x-payment", "payment-signature")
                       for k in c[2])]
        self.assertEqual(len(paid), 4)  # one paid retry per buy
        doc = json.loads(self.out.read_text())
        self.assertEqual(doc["data_kind"], "LIVE")
        self.assertEqual(doc["traps_sha256"], self.traps_sha256)
        self.assertIn("run", doc)
        self.assertTrue(doc["run"].startswith("run-"))
        self.assertEqual(doc["total_cost_usd"], 0.04)
        rows = doc["scores"]
        self.assertEqual(len(rows), 4)
        self.assertEqual({(r["trap_id"], r["provider_id"]) for r in rows},
                         {("t01-plain-transfer", "9002"),
                          ("t02-plain-transfer", "9002"),
                          ("t01-plain-transfer", "8453"),
                          ("t02-plain-transfer", "8453")})
        # Normalisation ran: t01 answers arrived as value_eth /
        # block_number and were scored against wei / int truth.
        t01 = [r for r in rows if r["trap_id"] == "t01-plain-transfer"]
        for r in t01:
            self.assertEqual(r["normalised_answer"]["value"],
                             "1000000000000000")
            self.assertEqual(r["normalised_answer"]["block"], 123)
            self.assertTrue(r["passed"])
            self.assertTrue(r["receipt_present"])
        # 8453 fails t02 on purpose (wrong status) — a real FAIL row.
        t02_8453 = [r for r in rows if r["trap_id"] == "t02-plain-transfer"
                    and r["provider_id"] == "8453"][0]
        self.assertFalse(t02_8453["passed"])
        # Leaderboard re-ranks from the same rows: 9002 (2/2) first.
        board = Leaderboard()
        by_id = {t["trap_id"]: t for t in (T01, T02)}
        for r in rows:
            trap = Trap(trap_id=r["trap_id"], intent=INTENT,
                        tx_hash=r["tx_hash"],
                        expected_status=by_id[r["trap_id"]]["expected_status"],
                        expected_from=by_id[r["trap_id"]]["expected_from"],
                        expected_to=by_id[r["trap_id"]]["expected_to"],
                        expected_value=by_id[r["trap_id"]]["expected_value"],
                        expected_block=by_id[r["trap_id"]]["expected_block"])
            board.add(score_answer(trap, r["provider_id"],
                                   r["normalised_answer"],
                                   cost_usd=r["cost_usd"],
                                   receipt_present=r["receipt_present"]))
        ranked = board.ranked()
        self.assertEqual([s.provider_id for s in ranked], ["9002", "8453"])
        self.assertEqual(ranked[0].passed, 2)
        self.assertEqual(ranked[1].passed, 1)


class TestRunnerNoOverwrite(RunnerTestBase):
    """(b) existing output file -> non-zero exit, file unchanged."""

    def test_existing_out_refused_without_append(self):
        self.out.write_text("SENTINEL — must not change")
        before = self.out.read_bytes()
        code, t = self._run()
        self.assertEqual(code, 6)
        self.assertEqual(self.out.read_bytes(), before)
        self.assertEqual(t.calls, [])  # refused before any network

    def test_existing_out_refused_for_dry_run_too(self):
        self.out.write_text("SENTINEL")
        code, t = self._run(["--dry-run"])
        self.assertEqual(code, 6)
        self.assertEqual(self.out.read_text(), "SENTINEL")


class TestRunnerMissingKey(RunnerTestBase):
    """(c) no key file -> non-zero exit with instructions, zero spend."""

    def test_missing_key_friendly_error(self):
        missing = self.dir / "no-such.key"
        err = io.StringIO()
        t = FakeTransport()
        with redirect_stderr(err):
            code = main(["--marker", str(self.marker),
                         "--traps", str(self.traps_path),
                         "--providers", "9002",
                         "--key", str(missing),
                         "--out", str(self.out)],
                        today=TODAY, transport=t,
                        balance_reader=_stub_balances,
                        receipt_verifier=_stub_receipts)
        self.assertEqual(code, 4)
        self.assertIn("KEY FILE MISSING", err.getvalue())
        self.assertIn("mint", err.getvalue())
        self.assertIn("PoW faucet", err.getvalue())
        self.assertIn(str(missing), err.getvalue())
        self.assertEqual(t.calls, [])  # no network, no spend
        self.assertFalse(self.out.exists())


class TestRunnerDryRun(RunnerTestBase):
    """(d) dry-run writes nothing and spends nothing."""

    def test_dry_run_validates_but_writes_and_buys_nothing(self):
        code, t = self._run(["--dry-run"])
        self.assertEqual(code, 0)
        self.assertFalse(self.out.exists())
        self.assertEqual(t.posts, [])  # no buys
        self.assertTrue(t.gets)  # catalogue fetch (free) did happen
        # A dry-run with an unknown provider still refuses.
        code, _ = self._run(["--dry-run"], transport=FakeTransport())
        self.assertEqual(code, 0)
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["--marker", str(self.marker),
                         "--traps", str(self.traps_path),
                         "--providers", "99999",
                         "--key", str(self.key),
                         "--out", str(self.out), "--dry-run"],
                        today=TODAY, transport=FakeTransport(),
                        balance_reader=_stub_balances,
                        receipt_verifier=_stub_receipts)
        self.assertEqual(code, 5)
        self.assertIn("not in the freshly fetched catalogue", err.getvalue())


class TestRunnerAppendNoDuplicates(RunnerTestBase):
    """(e) a second run with the same traps appends no duplicate rows."""

    def test_second_run_appends_no_duplicates_and_buys_nothing(self):
        code1, t1 = self._run(["--append"])
        self.assertEqual(code1, 0)
        doc1 = json.loads(self.out.read_text())
        self.assertEqual(len(doc1["scores"]), 4)
        code2, t2 = self._run(["--append"])
        self.assertEqual(code2, 0)
        doc2 = json.loads(self.out.read_text())
        self.assertEqual(len(doc2["scores"]), 4)
        pairs = [(r["trap_id"], r["provider_id"]) for r in doc2["scores"]]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(len(doc2["run_ids"]), 2)
        self.assertNotEqual(doc2["run_ids"][0], doc2["run_ids"][1])
        self.assertEqual(t2.posts, [])  # nothing re-bought
        self.assertEqual(doc2["total_cost_usd"], 0.04)

    def test_append_with_different_trap_set_refused(self):
        code1, _ = self._run(["--append"])
        self.assertEqual(code1, 0)
        other = self.dir / "other-traps.json"
        other.write_text(json.dumps({
            "intent": INTENT,
            "traps": [dict(T01, trap_id="t99-other")]}))
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["--marker", str(self.marker),
                         "--traps", str(other),
                         "--providers", "9002",
                         "--key", str(self.key),
                         "--out", str(self.out), "--append"],
                        today=TODAY, transport=FakeTransport(),
                        balance_reader=_stub_balances,
                        receipt_verifier=_stub_receipts)
        self.assertEqual(code, 7)
        self.assertIn("different trap set", err.getvalue())
        self.assertEqual(len(json.loads(self.out.read_text())["scores"]), 4)


if __name__ == "__main__":
    unittest.main()
