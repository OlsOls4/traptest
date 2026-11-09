"""Shared live-run harness — the single implementation of the
transport, Sepolia RPC, balance, row-building and receipt-verification
helpers used by the parametrised runner (traptest/run.py) and the two
historical scripts (scripts/full_run.py, scripts/mini_run.py).

Created by extracting the ~150 duplicated lines from those scripts
(Council finding F-dup): the two copies had diverged — only
mini_run.py recorded escrow credit, and only full_run.py's fail_row
lacked it. There is now one ``fail_row`` and one ``curl_transport``;
a fix here reaches every runner.

Nothing in this module spends anything: the only network calls are
the engine transport (injected by callers; the live default is curl),
free Sepolia JSON-RPC reads (balances, receipt batch), and receipt
verification. Payment happens only inside the caller's
DirectAskClient via its payment provider.
"""
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from .normalise import normalise
from .providers import USER_AGENT, TransportHTTPError, _HttpResponse
from .receipts import (
    SETTLEMENT_PAY_TO, SETTLEMENT_TOKEN, decode_receipt_tx_hash,
    parse_json_text, verify_receipt_batch)
from .scoring import score_answer
from .traps import Trap

# Live settlement constants (6 Nov 2026 run; also in traptest/receipts.py
# as SETTLEMENT_TOKEN / SETTLEMENT_PAY_TO — keep in sync).
TOKEN = SETTLEMENT_TOKEN
PAY_TO = SETTLEMENT_PAY_TO
BURNER = "0x170DfA67D1e37915d8130eaB9bD3b0a4E115f0C0"
SEPOLIA_RPC = "https://ethereum-sepolia-rpc.publicnode.com"
# $0.01 per call in 6-decimal USDC; a failed call can still settle
# this amount into Telegraph escrow credit (observed 6 Nov 2026).
CALL_PRICE_USD = 0.01

KEY_SETUP_INSTRUCTIONS = """\
KEY FILE MISSING: {key}

No purchase was made and nothing was spent. To run the live loop you
need a burner wallet holding Telegraph's accepted test USDC:

1. Create a burner wallet (a disposable testnet-only key, never a real
   wallet, never mainnet). Save its private key (hex, 0x-prefixed) to:
       {key}
   (mode 600, never committed — .burner*.key is gitignored).
2. Fund it with Sepolia ETH for gas: the PoW faucet
   (https://sepolia-faucet.pk910.de — mine a small amount, no account).
3. Mint the accepted test USDC yourself — there is NO Telegraph faucet.
   The accepted token is 0xcc194e1a843B658526D0D5C431f670028582Ae17 on
   Ethereum Sepolia; it has an open mint function, so call mint()
   for your burner address (e.g. 30 USDC). This is NOT Circle faucet
   USDC (0x1c7d4b196cb0c7b01d743fbc6116a902379c7238) — signing for
   that token is rejected by the facilitator.
4. Re-run with --key {key} (or pass --key <your key file>).

Each trap costs $0.01 of test USDC at most; the run stops at the
spend cap (default $0.30). A failed call can still settle $0.01
into Telegraph escrow credit — see docs/how-to-run.md §4.
"""


class MissingKeyError(FileNotFoundError):
    """Key file absent: friendly setup instructions, never a bare traceback."""


def read_key_file(path):
    """Read a burner private key, or raise MissingKeyError with the
    exact setup instructions (never an unhandled FileNotFoundError on
    a fresh clone). The key is returned only; never written or logged."""
    path = Path(path)
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        raise MissingKeyError(KEY_SETUP_INSTRUCTIONS.format(key=path)) from None


def sha256_file(path):
    """Hex sha256 of a file's bytes (recorded in every results file)."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def curl_transport(method, url, body, headers):
    """Engine transport over curl (150s cap). Raises TransportHTTPError
    on status 0 (no response) or >= 400, mirroring the old scripts."""
    hdrs = {**(headers or {}), "User-Agent": USER_AGENT}
    with tempfile.TemporaryDirectory() as d:
        hfile, bfile = f"{d}/h", f"{d}/b"
        cmd = ["curl", "-sS", "-m", "150", "-D", hfile, "-o", bfile,
               "-w", "%{http_code}", "-X", method, url]
        for k, v in hdrs.items():
            cmd += ["-H", f"{k}: {v}"]
        if body:
            cmd += ["--data-binary", "@-"]
        proc = subprocess.run(cmd, input=body, capture_output=True, timeout=180)
        status = int(proc.stdout.decode().strip() or 0)
        raw_headers = Path(hfile).read_text(errors="replace") if Path(hfile).exists() else ""
        parsed = {}
        for line in raw_headers.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                parsed[k.strip()] = v.strip()
        resp_body = Path(bfile).read_bytes() if Path(bfile).exists() else b""
        if status == 0:
            raise TransportHTTPError(0, proc.stderr[:500], parsed)
        if status >= 400:
            raise TransportHTTPError(status, resp_body, parsed)
        return _HttpResponse(status, resp_body, parsed)


def sep_rpc(method, params, rpc_url=SEPOLIA_RPC):
    """One Sepolia JSON-RPC call (free read). Raises on an RPC error."""
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    r = subprocess.run(["curl", "-sS", "-m", "30", rpc_url,
                        "-H", "Content-Type: application/json", "-d", payload],
                       capture_output=True, text=True, timeout=60)
    d = parse_json_text(r.stdout, f"Sepolia RPC {method} response")
    if "error" in d:
        raise RuntimeError(d["error"])
    return d["result"]


def token_balance(addr, rpc_url=SEPOLIA_RPC):
    """Accepted-test-USDC balance of an address, in whole USDC (6 decimals)."""
    data = "0x70a08231" + addr[2:].rjust(64, "0")
    return int(sep_rpc("eth_call", [{"to": TOKEN, "data": data}, "latest"],
                       rpc_url=rpc_url), 16) / 1e6


def eth_balance(addr, rpc_url=SEPOLIA_RPC):
    """Sepolia ETH balance of an address, in whole ETH."""
    return int(sep_rpc("eth_getBalance", [addr, "latest"],
                       rpc_url=rpc_url), 16) / 1e18


def atomic_write_text(path, text):
    """Write ``text`` to ``path`` atomically: temp file in the same
    directory + fsync + rename + directory fsync. A crash mid-write
    leaves either the old file or the new one, never a torn half-file
    (F8 — the runner's per-row save must not corrupt the results file
    if the process dies between rows)."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent),
                               prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        dfd = os.open(str(path.parent), os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _payment_status(error):
    """``payment.status`` from the JSON payload embedded in an error
    string, or None.

    The live error is ``PurchaseFailedError: Ask failed (status 500):
    {json}`` and the runner truncates it to 300 chars, so the JSON is
    usually cut mid-string (the 24 live escrow rows end inside the
    ``message`` value). Parse it structurally: json.loads when whole,
    else repair the truncation by closing the open string and the
    open objects and parse that. The status is read from the parsed
    ``payment`` object's ``status`` field — never from a bare
    substring search for "escrow" in free text (the old bug: any error
    mentioning escrow, e.g. "escrow service unavailable", was credited
    $0.01 it never settled). Only the exact status
    ``escrow_credit_pending`` counts; anything else (or no payment
    object at all) returns None.
    """
    if not error:
        return None
    start = error.find("{")
    if start < 0:
        return None
    payload = error[start:]
    for candidate in (payload,
                      *(payload + q + "}" * n
                        for q in ("", '"') for n in range(0, 5))):
        try:
            doc = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(doc, dict):
            payment = doc.get("payment")
            if isinstance(payment, dict):
                return payment.get("status")
            return None
    return None


def _truncate_error_for_storage(error):
    """The stored ``error`` field keeps the historical format exactly:
    ``"<TypeName>: "`` + the first 300 chars of the detail — the same
    truncation the runner used to apply before calling fail_row. The
    parse in :func:`_payment_status` runs on the FULL string passed
    in, so a long nested upstream message can no longer push the
    ``payment`` object past the cut (the live OnChain Intel rows lost
    exactly that evidence to the 300-char cut; their credits survive
    in the frozen files from the post-hoc balance repair, not from
    this string)."""
    if error is None:
        return None
    if ": " in error:
        head, detail = error.split(": ", 1)
        return f"{head}: {detail[:300]}"
    return error


def fail_row(trap, miner_id, error):
    """A scored row for a call that produced no answer.

    ``cost_usd`` is 0 (not billed for a served answer) — but a failed
    call can still settle $0.01 on-chain into Telegraph escrow credit,
    so the row records ``escrow_credit_usd`` at write time whenever
    the error's JSON payload says so (``payment.status ==
    "escrow_credit_pending"``, parsed structurally from the FULL
    error string — see :func:`_payment_status`), instead of assuming
    the call cost $0. The stored ``error`` field keeps the historical
    300-char-detail truncation (see
    :func:`_truncate_error_for_storage`), so the live data format is
    unchanged. The on-chain Transfer to payTo is the evidence; the
    row records it so balance drops are never unexplained. Per-call
    on-chain escrow settlement verification is OUT of scope: this
    records what the engine's error payload reports, it does not
    re-verify the settlement transaction on-chain.
    """
    row = {"data_kind": "LIVE", "trap_id": trap.trap_id,
           "provider_id": miner_id, "passed": False,
           "cost_usd": 0, "signal_hash": None, "receipt_present": False,
           "receipt": None, "charged": False, "answer": None,
           "normalised_answer": None, "normalisation_notes": [],
           "fields": [], "error": _truncate_error_for_storage(error)}
    if _payment_status(error) == "escrow_credit_pending":
        row["escrow_credit_usd"] = CALL_PRICE_USD
    return row


def build_scored_row(trap, trap_dict, miner_id, intent, result):
    """Normalise + score one served answer into its results row.

    The raw answer is always kept alongside the normalised one, so
    every score stays auditable.
    """
    norm, notes = normalise(result.answer)
    score = score_answer(trap, miner_id, norm, cost_usd=result.cost_usd,
                         signal_hash=result.signal_hash,
                         receipt_present=bool(result.receipt))
    return {
        "data_kind": "LIVE",
        "trap_id": trap.trap_id,
        "category": trap_dict.get("category"),
        "intent": intent,
        "tx_hash": trap.tx_hash,
        # Scoring version for this row: "v2-strict-unknown" only on
        # traps that opt into the v2 unknown rule (expansion set,
        # 9 Nov 2026); every other trap scores under v1, byte-identical
        # to the frozen-12 run. The token-value basis change in the
        # expansion set is a trap-design change, recorded on the trap
        # file, not a scorer change.
        "scoring_version": ("v2-strict-unknown" if getattr(trap, "strict_unknown", False)
                            else "v1"),
        "provider_id": miner_id,
        "cost_usd": result.cost_usd,
        "signal_hash": result.signal_hash,
        "receipt_present": bool(result.receipt),
        "receipt": result.receipt,
        "charged": result.charged,
        "answer": result.answer,
        "normalised_answer": norm,
        "normalisation_notes": notes,
        "passed": score.passed,
        "fields": [{"field": f.field, "expected": f.expected,
                    "actual": f.actual, "passed": f.passed}
                   for f in score.fields],
    }


def load_traps(path):
    """Load a trap-set JSON file -> (doc dict, [Trap], sha256 hex).

    Validates via :func:`traptest.trap_catalog.build_fixed_set` with
    the provenance parsed from the trap file itself: every trap must
    carry a ``provenance`` object ({source, source_url, block,
    checked_at, checker, notes}) and a ``category``; the set must
    contain the mandatory categories (reverted_tx, unknown_tx), stay
    within MAX_TRAPS (30), and contain no pending trap (a pending
    transaction's ground truth changes when it confirms, so it can
    never be a fixed trap). A file failing any of these raises
    ValueError — the runner turns that into exit 3 before any network
    call or spend. The sha256 is recorded in every results file the
    runner writes.
    """
    from .trap_catalog import GroundTruthProvenance, build_fixed_set

    path = Path(path)
    raw = path.read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    traps_raw = doc["traps"]
    entries = []
    for t in traps_raw:
        trap = Trap(trap_id=t["trap_id"], intent=t["intent"], tx_hash=t["tx_hash"],
                    expected_status=t["expected_status"], expected_from=t["expected_from"],
                    expected_to=t["expected_to"], expected_value=t["expected_value"],
                    expected_block=t["expected_block"],
                    strict_unknown=bool(t.get("strict_unknown", False)))
        if trap.expected_status == "pending":
            raise ValueError(
                f"trap {trap.trap_id!r}: pending transactions are never "
                f"fixed traps — their ground truth changes when they confirm")
        prov_raw = t.get("provenance")
        if not isinstance(prov_raw, dict):
            raise ValueError(
                f"trap {trap.trap_id!r}: missing provenance — every trap "
                f"in a fixed set must record how its ground truth was "
                f"checked against public chain data (provenance object "
                f"with source, source_url, block, checked_at, checker)")
        prov = GroundTruthProvenance(
            trap_id=t["trap_id"],
            category=t.get("category") or "",
            source_name=prov_raw.get("source") or "",
            source_url=prov_raw.get("source_url") or "",
            tx_reference=t["tx_hash"],
            block_reference=prov_raw.get("block"),
            checked_at=prov_raw.get("checked_at") or "",
            checker=prov_raw.get("checker") or "",
            notes=prov_raw.get("notes") or "")
        entries.append((trap, prov))
    traps = build_fixed_set(entries)
    return doc, traps, hashlib.sha256(raw).hexdigest()


def verify_receipts(rows, rpc_url=SEPOLIA_RPC):
    """Verify settlement receipts on-chain (Sepolia) in one batch.

    A receipt verifies only when the settlement tx succeeded AND its
    Transfer log paid the exact amount ($0.01 / 10000 atomic) to the
    exact payTo — see traptest/receipts.py. The request list is
    filtered BEFORE batching, so ids line up with responses and a
    short response raises instead of silently truncating. Mutates the
    rows in place; returns (verified, total).
    """
    tx_hashes = []
    for row in rows:
        if row.get("receipt"):
            tx_hash = decode_receipt_tx_hash(row["receipt"])
            if tx_hash:
                tx_hashes.append((row["trap_id"], row["provider_id"], tx_hash))
    if not tx_hashes:
        return 0, 0
    payload = json.dumps([{"jsonrpc": "2.0", "id": i, "method": "eth_getTransactionReceipt",
                           "params": [h]} for i, (_, _, h) in enumerate(tx_hashes)])
    r = subprocess.run(["curl", "-sS", "-m", "60", rpc_url,
                        "-H", "Content-Type: application/json", "-d", payload],
                       capture_output=True, text=True, timeout=90)
    recs = parse_json_text(r.stdout, "Sepolia receipt batch response")
    if not isinstance(recs, list):
        raise RuntimeError("receipt batch response was not a JSON list")
    verified = verify_receipt_batch(tx_hashes, recs)
    tx_by_key = {(t, m): h for t, m, h in tx_hashes}
    for row in rows:
        key = (row.get("trap_id"), row.get("provider_id"))
        if key in verified:
            row["receipt_verified_onchain"] = verified[key]
            if verified[key]:
                row["receipt_settlement_tx"] = tx_by_key[key]
    return sum(verified.values()), len(verified)
