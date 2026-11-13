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
    "provenance": {
        "source": "Mock Explorer",
        "source_url": "https://example.invalid/tx/mock-t01",
        "block": 123, "checked_at": "2026-11-06",
        "checker": "mock-checker",
        "notes": "mock fixture, NOT event evidence",
    },
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
    "provenance": {
        "source": "Mock Explorer",
        "source_url": "https://example.invalid/tx/mock-t02",
        "block": 456, "checked_at": "2026-11-06",
        "checker": "mock-checker",
        "notes": "mock fixture, NOT event evidence",
    },
}
T03 = {
    "trap_id": "t03-reverted-tx",
    "category": "reverted_tx",
    "intent": INTENT,
    "tx_hash": "0x" + "33" * 32,
    "expected_status": "reverted",
    "expected_from": "0x" + "55" * 20,
    "expected_to": "0x" + "66" * 20,
    "expected_value": None,
    "expected_block": 789,
    "provenance": {
        "source": "Mock Explorer",
        "source_url": "https://example.invalid/tx/mock-t03",
        "block": 789, "checked_at": "2026-11-06",
        "checker": "mock-checker",
        "notes": "mock fixture, NOT event evidence",
    },
}
T04 = {
    "trap_id": "t04-unknown-tx",
    "category": "unknown_tx",
    "intent": INTENT,
    "tx_hash": "0x" + "44" * 32,
    "expected_status": "not_found",
    "expected_from": None,
    "expected_to": None,
    "expected_value": None,
    "expected_block": None,
    "provenance": {
        "source": "Mock Explorer",
        "source_url": "https://example.invalid/tx/mock-t04-search",
        "block": None, "checked_at": "2026-11-06",
        "checker": "mock-checker",
        "notes": "mock fixture: explorer search returned no record",
    },
}
ALL_TRAPS = (T01, T02, T03, T04)
BY_TX = {t["tx_hash"]: t for t in ALL_TRAPS}


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
            trap = BY_TX[tx]
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
            elif tx == T03["tx_hash"]:
                answer = {"status": "reverted",
                          "from": trap["expected_from"],
                          "to": trap["expected_to"],
                          "block": 789}
            elif tx == T02["tx_hash"]:
                answer = {"status": "confirmed",
                          "from": trap["expected_from"],
                          "to": trap["expected_to"],
                          "value": "0", "block": 456}
            else:  # T04 unknown_tx: any invented field would fail.
                answer = {"status": "not_found"}
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
            "intent": INTENT, "traps": list(ALL_TRAPS)}, indent=2))
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
        call_kwargs = dict(balance_reader=_stub_balances,
                           receipt_verifier=_stub_receipts)
        call_kwargs.update(kwargs)  # callers may override either stub
        code = main(self._args(extra), today=TODAY, transport=transport,
                    **call_kwargs)
        return code, transport


class TestRunnerEndToEnd(RunnerTestBase):
    """(a) freeze -> buy (fake transport, no network, no spend) ->
    score -> leaderboard, using the new runner."""

    def test_freeze_buy_score_leaderboard(self):
        code, t = self._run()
        self.assertEqual(code, 0)
        # Buys happened only via the fake transport: 8 buys x 2 POSTs
        # (402 challenge, then paid retry).
        self.assertEqual(len(t.posts), 16)
        paid = [c for c in t.posts
                if any(k.lower() in ("x-payment", "payment-signature")
                       for k in c[2])]
        self.assertEqual(len(paid), 8)  # one paid retry per buy
        # F12: the catalogue was fetched ONCE for provider resolution;
        # each buy reuses its pre-fetched entry, no re-fetch per buy.
        self.assertEqual(len(t.gets), 1)
        doc = json.loads(self.out.read_text())
        self.assertEqual(doc["data_kind"], "LIVE")
        self.assertEqual(doc["traps_sha256"], self.traps_sha256)
        self.assertIn("run", doc)
        self.assertTrue(doc["run"].startswith("run-"))
        self.assertEqual(doc["total_cost_usd"], 0.08)
        rows = doc["scores"]
        self.assertEqual(len(rows), 8)
        self.assertEqual({(r["trap_id"], r["provider_id"]) for r in rows},
                         {(trap["trap_id"], mid)
                          for trap in ALL_TRAPS
                          for mid in ("9002", "8453")})
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
        # Leaderboard re-ranks from the same rows: 9002 (4/4) first.
        board = Leaderboard()
        by_id = {t["trap_id"]: t for t in ALL_TRAPS}
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
        self.assertEqual(ranked[0].passed, 4)
        self.assertEqual(ranked[1].passed, 3)


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
        self.assertEqual(len(doc1["scores"]), 8)
        code2, t2 = self._run(["--append"])
        self.assertEqual(code2, 0)
        doc2 = json.loads(self.out.read_text())
        self.assertEqual(len(doc2["scores"]), 8)
        pairs = [(r["trap_id"], r["provider_id"]) for r in doc2["scores"]]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(len(doc2["run_ids"]), 2)
        self.assertNotEqual(doc2["run_ids"][0], doc2["run_ids"][1])
        self.assertEqual(t2.posts, [])  # nothing re-bought
        self.assertEqual(doc2["total_cost_usd"], 0.08)

    def test_append_with_different_trap_set_refused(self):
        code1, _ = self._run(["--append"])
        self.assertEqual(code1, 0)
        other = self.dir / "other-traps.json"
        # A different but PROVENANCE-VALID trap set (one id renamed),
        # so the refusal comes from the sha256 mismatch, not the
        # provenance gate (exit 7, not 3).
        other.write_text(json.dumps({
            "intent": INTENT,
            "traps": [dict(T01, trap_id="t99-other"), T02, T03, T04]}))
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
        self.assertEqual(len(json.loads(self.out.read_text())["scores"]), 8)


class TestRunnerProvenanceEnforcement(RunnerTestBase):
    """(F3) a trap set without provenance, with a pending trap, without
    a mandatory category, or over MAX_TRAPS exits 3 before any network
    call — the provenance gate runs before the catalogue fetch."""

    def _write_traps(self, traps):
        path = self.dir / "bad-traps.json"
        path.write_text(json.dumps({"intent": INTENT, "traps": traps}))
        return path

    def _run_with_traps(self, traps_path):
        err = io.StringIO()
        t = FakeTransport()
        with redirect_stderr(err):
            code = main(["--marker", str(self.marker),
                         "--traps", str(traps_path),
                         "--providers", "9002",
                         "--key", str(self.key),
                         "--out", str(self.out)],
                        today=TODAY, transport=t,
                        balance_reader=_stub_balances,
                        receipt_verifier=_stub_receipts)
        return code, t, err.getvalue()

    def test_provenance_less_trap_set_exits_3_before_network(self):
        bare = [dict(t) for t in ALL_TRAPS]
        for t in bare:
            t.pop("provenance", None)
        code, t, err = self._run_with_traps(self._write_traps(bare))
        self.assertEqual(code, 3)
        self.assertIn("provenance", err)
        self.assertEqual(t.calls, [])
        self.assertFalse(self.out.exists())

    def test_pending_trap_exits_3_before_network(self):
        pending = dict(T01, expected_status="pending")
        code, t, err = self._run_with_traps(
            self._write_traps([pending, T03, T04]))
        self.assertEqual(code, 3)
        self.assertIn("pending", err)
        self.assertEqual(t.calls, [])

    def test_missing_mandatory_category_exits_3_before_network(self):
        code, t, err = self._run_with_traps(self._write_traps([T01, T02]))
        self.assertEqual(code, 3)
        self.assertIn("mandatory", err)
        self.assertEqual(t.calls, [])

    def test_over_max_traps_exits_3_before_network(self):
        traps = []
        for i in range(30):
            traps.append(dict(
                T03, trap_id=f"t-r{i:02d}",
                tx_hash="0x" + f"{i:02x}" * 32,
                provenance=dict(T03["provenance"], block=789 + i)))
        traps.append(dict(T04, trap_id="t-u30",
                          tx_hash="0x" + "ff" * 32))
        self.assertEqual(len(traps), 31)
        code, t, err = self._run_with_traps(self._write_traps(traps))
        self.assertEqual(code, 3)
        self.assertIn("over the cap", err)
        self.assertEqual(t.calls, [])


class TestRunnerReceiptVerificationPersisted(RunnerTestBase):
    """(9 Nov 2026) receipt verification flags must survive in the
    output file: the verifier mutates the in-memory rows, and the
    final doc rewrite used to re-read the file from disk, silently
    discarding every receipt_verified_onchain flag (the 8 Nov replay
    file and the expansion files all showed zero flags despite
    '24/24 settled' logs)."""

    def test_verification_flags_persisted_in_output_file(self):
        def verifying_verifier(rows):
            verified = 0
            for r in rows:
                if r.get("receipt_present"):
                    r["receipt_verified_onchain"] = True
                    r["receipt_settlement_tx"] = "0x" + "ab" * 32
                    verified += 1
            return verified, len(rows)

        code, t = self._run(receipt_verifier=verifying_verifier)
        self.assertEqual(code, 0)
        doc = json.loads(self.out.read_text())
        served = [r for r in doc["scores"] if r["receipt_present"]]
        self.assertEqual(len(served), 8)
        for r in served:
            self.assertTrue(r.get("receipt_verified_onchain"), r["trap_id"])
            self.assertEqual(r.get("receipt_settlement_tx"), "0x" + "ab" * 32)


class TestRunnerPostLoopFailures(RunnerTestBase):
    """(F8) receipt verification / balance read failures after the buy
    loop exit non-zero CLEANLY: rows stay saved, the error is recorded
    in the output doc, no traceback escapes."""

    def test_receipt_verifier_failure_exits_8_with_error_recorded(self):
        def boom(rows):
            raise RuntimeError("Sepolia RPC down")

        err = io.StringIO()
        with redirect_stderr(err):
            code, t = self._run(receipt_verifier=boom)
        self.assertEqual(code, 8)
        self.assertNotIn("Traceback", err.getvalue())
        doc = json.loads(self.out.read_text())
        self.assertEqual(len(doc["scores"]), 8)  # rows survived
        self.assertEqual(doc["total_cost_usd"], 0.08)
        self.assertIn("receipt_verification_error", doc)
        self.assertIn("Sepolia RPC down",
                      doc["receipt_verification_error"])
        self.assertIn("burner_balance_after_usdc", doc)  # balances ok

    def test_balance_reader_failure_exits_8_with_error_recorded(self):
        # Fail only the POST-loop read: the pre-loop read (before any
        # buy) succeeds, the after-read fails.
        calls = []

        def boom(addr):
            calls.append(addr)
            if len(calls) > 1:
                raise RuntimeError("Sepolia RPC down")
            return 30.0, 0.05

        err = io.StringIO()
        with redirect_stderr(err):
            code, t = self._run(balance_reader=boom)
        self.assertEqual(code, 8)
        self.assertNotIn("Traceback", err.getvalue())
        doc = json.loads(self.out.read_text())
        self.assertEqual(len(doc["scores"]), 8)
        self.assertIn("balance_read_error", doc)
        self.assertIn("Sepolia RPC down", doc["balance_read_error"])
        self.assertNotIn("burner_balance_after_usdc", doc)
        self.assertNotIn("balance_drop_usdc", doc)


class TestRunnerSpendGuard(RunnerTestBase):
    """(F4) the cap is charged against the live challenge amount, not
    the assumed $0.01: a $0.02 challenge against a $0.015 remaining
    cap is refused before any payment is attempted."""

    def test_challenge_above_remaining_cap_refused_without_payment(self):
        class PriceyTransport(FakeTransport):
            def __call__(self, method, url, body, headers):
                self.calls.append((method, url, dict(headers or {}), body))
                if method == "GET" and url.endswith(f"/intents/{INTENT}/miners"):
                    return _HttpResponse(200, _json_body({"miners": [
                        {"id": "9002", "name": "TxLens", "cost_per_call": "0.00"},
                        {"id": "8453", "name": "Truvian", "cost_per_call": "0.00"},
                    ]}), {"Content-Type": "application/json"})
                if method == "POST" and "/v1/ask/" in url:
                    raise TransportHTTPError(402, _json_body(
                        {"amount_usd": 0.02, "payTo": PAY_TO,
                         "asset": ASSET, "network": "eip155:11155111"}), {})
                raise AssertionError(f"unexpected call {method} {url}")

        t = PriceyTransport()
        code = main(self._args(["--spend-cap", "0.015"]), today=TODAY,
                    transport=t, balance_reader=_stub_balances,
                    receipt_verifier=_stub_receipts)
        self.assertEqual(code, 0)
        # No paid retry was ever attempted: the guard refused the
        # $0.02 challenge before the signer was invoked.
        paid = [c for c in t.posts
                if any(k.lower() in ("x-payment", "payment-signature")
                       for k in c[2])]
        self.assertEqual(paid, [])
        doc = json.loads(self.out.read_text())
        self.assertEqual(doc["total_cost_usd"], 0)
        self.assertTrue(all("spend cap" in (r.get("error") or "")
                            for r in doc["scores"]))
        self.assertEqual(len(doc["scores"]), 8)


class TestDryRunGateScoping(RunnerTestBase):
    """(13 Nov 2026) --dry-run bypasses the marker; with a missing
    key it still fails cleanly (exit 4, instructions, no traceback)."""

    def test_dry_run_bypasses_missing_marker(self):
        missing_marker = self.dir / "NO-MARKER"
        code, t = self._run(["--dry-run", "--marker", str(missing_marker)])
        # _run() passes --marker self.marker; the later --marker wins.
        self.assertEqual(code, 0)
        self.assertFalse(self.out.exists())
        self.assertEqual(t.posts, [])

    def test_dry_run_missing_key_clean_error_no_marker(self):
        missing_marker = self.dir / "NO-MARKER"
        missing_key = self.dir / "no-such.key"
        err = io.StringIO()
        t = FakeTransport()
        with redirect_stderr(err):
            code = main(["--marker", str(missing_marker),
                         "--traps", str(self.traps_path),
                         "--providers", "9002",
                         "--key", str(missing_key),
                         "--out", str(self.out), "--dry-run"],
                        today=TODAY, transport=t,
                        balance_reader=_stub_balances,
                        receipt_verifier=_stub_receipts)
        self.assertEqual(code, 4)
        self.assertIn("KEY FILE MISSING", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(t.calls, [])  # no network, no spend
        self.assertFalse(self.out.exists())


class TestBurnerBalanceAddress(RunnerTestBase):
    """(13 Nov 2026) balance reporting follows the --key actually
    used: the output file records that key's payer address, and the
    balance reader is called with it — never the hardcoded burner 3."""

    def test_balance_uses_key_payer_address(self):
        other_key = self.dir / "other-burner.key"
        other_key.write_text("0x" + Account.create().key.hex())
        expected = Account.from_key(other_key.read_text().strip()).address
        self.assertNotEqual(expected, "0x170DfA67D1e37915d8130eaB9bD3b0a4E115f0C0")
        seen = []

        def reader(addr):
            seen.append(addr)
            return 12.5, 0.01

        code = main(self._args(["--key", str(other_key)]), today=TODAY,
                    transport=FakeTransport(), balance_reader=reader,
                    receipt_verifier=_stub_receipts)
        self.assertEqual(code, 0)
        self.assertTrue(seen)
        self.assertTrue(all(a == expected for a in seen), seen)
        doc = json.loads(self.out.read_text())
        self.assertEqual(doc["burner_address"], expected)
        self.assertEqual(doc["burner_balance_before_usdc"], 12.5)
        self.assertEqual(doc["burner_balance_after_usdc"], 12.5)


class TestCapSkippedRetryable(RunnerTestBase):
    """(13 Nov 2026) cap-skipped rows are not scored pairs: a re-run
    with a raised cap re-buys them, replacing the stale skipped row
    instead of duplicating the (trap, provider) pair."""

    def test_cap_skipped_pairs_rebought_with_raised_cap(self):
        # $0.015 cap: 1 buy ($0.01), then 7 cap-skipped rows.
        code1, _ = self._run(["--spend-cap", "0.015"])
        self.assertEqual(code1, 0)
        doc1 = json.loads(self.out.read_text())
        skipped = [r for r in doc1["scores"] if r.get("skipped_cap")]
        self.assertEqual(len(skipped), 7)
        self.assertEqual(len(doc1["scores"]), 8)
        # Raised cap + --append: the 7 skipped pairs are bought now.
        code2, t2 = self._run(["--append", "--spend-cap", "0.30"])
        self.assertEqual(code2, 0)
        doc2 = json.loads(self.out.read_text())
        self.assertEqual(len(doc2["scores"]), 8)
        self.assertFalse(any(r.get("skipped_cap") for r in doc2["scores"]))
        pairs = [(r["trap_id"], r["provider_id"]) for r in doc2["scores"]]
        self.assertEqual(len(pairs), len(set(pairs)))  # no duplicates
        self.assertEqual(doc2["total_cost_usd"], 0.08)
        self.assertEqual(len(t2.posts), 14)  # 7 buys x 402 + paid retry

    def test_dry_run_counts_cap_skipped_pairs_as_new(self):
        self._run(["--spend-cap", "0.015"])
        code, _ = self._run(["--append", "--spend-cap", "0.30", "--dry-run"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
