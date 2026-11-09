"""Freeze the 12-trap EXPANSION set for 9 Nov 2026 (t13-t24).

ADDITIVE ONLY: the frozen 12 (traps-frozen-2026-11-06.json) are never
touched. This script scans recent Base Sepolia blocks via curl-backed
JSON-RPC (publicnode), classifies transactions into the six categories
(2 each), verifies ground truth from tx + receipt data, and writes
traps-frozen-2026-11-09.json. Run once, before any scored purchase
against this set. Never re-run after scoring starts.

Scoring v2 (this set ONLY — disclosed, never retroactive):
- token_transfer traps score the NATIVE tx value field (raw wei),
  NOT the Transfer-event amount. The frozen t03/t04 scored the event
  amount, which no provider returns in `value` — unwinnable in
  practice. If the native value is 0, expected_value is "0" explicitly
  (scored, passable). The first Transfer amount is recorded in notes
  as unscored context only.
- contract_interaction traps are non-zero-value, log-bearing calls;
  value is left unscored (log amounts are not scored by the schema)
  and the trap notes say so.
- multi_recipient traps need 3+ distinct recipients; the recipient
  list is a note, not scored (schema has no list field).
- unknown_tx traps carry strict_unknown=true: a not_found answer
  carrying any invented from/to/value/block fails outright (v2 rule
  in traptest/scoring.py; frozen-12 scoring is byte-identical).
"""
import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_RPC = "https://base-sepolia-rpc.publicnode.com"
INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
OUT = Path(__file__).resolve().parent.parent / "traps-frozen-2026-11-09.json"
LARGE_VALUE_WEI = 10 ** 16  # plain-transfer "large": >= 0.01 ETH


def rpc_batch(calls):
    """calls: list of (method, params). Returns list of results."""
    payload = json.dumps([{"jsonrpc": "2.0", "id": i, "method": m, "params": p}
                          for i, (m, p) in enumerate(calls)])
    for attempt in range(4):
        r = subprocess.run(["curl", "-sS", "-m", "60", BASE_RPC,
                            "-H", "Content-Type: application/json",
                            "-d", payload], capture_output=True, text=True, timeout=90)
        try:
            data = json.loads(r.stdout)
            return [d.get("result") if isinstance(d, dict) else None for d in data]
        except Exception:
            if attempt == 3:
                raise RuntimeError(f"RPC batch failed: {r.stdout[:300]} {r.stderr[:300]}")
    raise RuntimeError("unreachable")


def rpc(method, params):
    return rpc_batch([(method, params)])[0]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def wei_str(hexval):
    return str(int(hexval, 16)) if hexval else "0"


def has_code(addr):
    code = rpc("eth_getCode", [addr, "latest"])
    return bool(code and code != "0x")


def mk(t, r, category, checked_at, value=None, value_basis=None, extra_notes="",
       strict_unknown=False):
    """Build a trap record from live tx + receipt dicts."""
    status = "reverted" if r["status"] == "0x0" else "confirmed"
    v = value
    basis = value_basis or ("tx value field, raw wei" if v is not None else None)
    rec = {
        "trap_id": "tmp",
        "category": category,
        "intent": INTENT,
        "tx_hash": t["hash"],
        "expected_status": status,
        "expected_from": t["from"],
        "expected_to": t["to"],
        "expected_value": v,
        "expected_block": int(r["blockNumber"], 16),
        "value_basis": basis,
        "provenance": {
            "source": "Base Sepolia public RPC",
            "source_url": "https://base-sepolia-rpc.publicnode.com",
            "block": int(r["blockNumber"], 16),
            "checked_at": checked_at,
            "checker": "freeze script (curl JSON-RPC), 9 Nov 2026",
            "notes": extra_notes,
        },
    }
    if strict_unknown:
        rec["strict_unknown"] = True
    return rec


def main():
    checked_at = now_iso()
    latest = int(rpc("eth_blockNumber", []), 16)
    print(f"latest base sepolia block: {latest} (checked {checked_at})")

    found = {"token_transfer": [], "contract_interaction": [],
             "reverted_tx": [], "multi_recipient_tx": []}
    reverted_value = None      # reverted with non-zero value (scored)
    reverted_contract = None   # reverted contract call, value 0 (unscored)
    plain_candidates = []      # (value_wei, trap) with value >= 0.01 ETH

    def filled():
        return (len(found["token_transfer"]) >= 2
                and len(found["contract_interaction"]) >= 2
                and reverted_value is not None
                and reverted_contract is not None
                and len(found["multi_recipient_tx"]) >= 2
                and len(plain_candidates) >= 2)

    blk = latest
    scanned = 0
    CHUNK = 50  # blocks per batched RPC round: one curl per 50 blocks,
    # then batched receipt/tx fetches — per-block curls were ~20x slower
    while not filled() and scanned < 6000:
        block_nums = [blk - i for i in range(CHUNK)]
        blocks = rpc_batch([("eth_getBlockByNumber", [hex(n), False])
                            for n in block_nums])
        scanned += len(block_nums)
        blk -= CHUNK
        all_hashes = []
        for b in blocks:
            if b and b.get("transactions"):
                all_hashes.extend(b["transactions"])
        if not all_hashes:
            continue
        receipts, txs = [], []
        for i in range(0, len(all_hashes), 200):
            part = all_hashes[i:i + 200]
            receipts += rpc_batch([("eth_getTransactionReceipt", [h]) for h in part])
            txs += rpc_batch([("eth_getTransactionByHash", [h]) for h in part])
        # Batch the eth_getCode checks for every distinct `to` that
        # might be a contract candidate, in one call.
        code_addrs = sorted({t["to"] for t in txs if t and t.get("to")})
        codes = {}
        for i in range(0, len(code_addrs), 200):
            part = code_addrs[i:i + 200]
            res = rpc_batch([("eth_getCode", [a, "latest"]) for a in part])
            codes.update({a: (c and c != "0x") for a, c in zip(part, res)})
        for h, r, t in zip(all_hashes, receipts, txs):
            if not r or not t:
                continue
            status = r["status"]
            transfers = [l for l in r.get("logs", [])
                         if l["topics"] and l["topics"][0].lower() == TRANSFER_TOPIC]
            inp = t.get("input") or "0x"
            has_input = inp not in ("0x", "", None) and len(inp) > 2
            value_wei = int(t["value"], 16)
            if status == "0x0":
                if value_wei > 0 and reverted_value is None:
                    reverted_value = mk(t, r, "reverted_tx", checked_at,
                                        value=wei_str(t["value"]),
                                        value_basis="tx value field, raw wei",
                                        extra_notes="Receipt status 0x0; non-zero tx value scored.")
                    print(f"reverted+value: {h} block {int(r['blockNumber'], 16)} value={wei_str(t['value'])}")
                elif has_input and value_wei == 0 and reverted_contract is None \
                        and t.get("to") and codes.get(t["to"]):
                    reverted_contract = mk(t, r, "reverted_tx", checked_at,
                                           extra_notes="Receipt status 0x0; reverted contract call (code present at `to`); tx value 0, unscored.")
                    print(f"reverted+contract: {h} block {int(r['blockNumber'], 16)}")
            elif status == "0x1" and len(transfers) >= 1 \
                    and len(found["token_transfer"]) < 2 \
                    and inp.startswith(("0xa9059cbb", "0x23b872dd")):
                first = transfers[0]
                tr = mk(t, r, "token_transfer", checked_at,
                        value=wei_str(t["value"]),
                        value_basis="tx value field, raw wei (scoring v2: native value, NOT Transfer event amount)",
                        extra_notes=f"Scoring v2: expected_value is the NATIVE tx value ({wei_str(t['value'])} wei). Token contract {first['address']}; first Transfer event amount {int(first['data'], 16)} (raw token units) is recorded here as unscored context only — it is NOT the scored value. {len(transfers)} Transfer event(s) in receipt.")
                tr["token_contract"] = first["address"]
                found["token_transfer"].append(tr)
                print(f"token(v2 native): {h} block {int(r['blockNumber'], 16)} native={wei_str(t['value'])} event={int(first['data'], 16)}")
            elif status == "0x1" and len(transfers) >= 3 \
                    and len(found["multi_recipient_tx"]) < 2:
                recipients = {l["topics"][2].lower() for l in transfers
                              if len(l["topics"]) > 2}
                if len(recipients) >= 3:
                    found["multi_recipient_tx"].append(mk(
                        t, r, "multi_recipient_tx", checked_at,
                        extra_notes=f"{len(transfers)} Transfer events in receipt to {len(recipients)} distinct recipients; recipient list is a note, not scored."))
                    print(f"multi(3+): {h} block {int(r['blockNumber'], 16)} transfers={len(transfers)} recipients={len(recipients)}")
            elif status == "0x1" and has_input and transfers \
                    and value_wei > 0 \
                    and len(found["contract_interaction"]) < 2 \
                    and t.get("to") and codes.get(t["to"]):
                found["contract_interaction"].append(mk(
                    t, r, "contract_interaction", checked_at,
                    extra_notes=f"Non-zero-value ({wei_str(t['value'])} wei), log-bearing contract call (code present at `to`, {len(r.get('logs', []))} log(s)); tx value is UNSCORED — contract-call amounts live in logs, which this schema does not score."))
                print(f"contract: {h} block {int(r['blockNumber'], 16)} value={wei_str(t['value'])} logs={len(r.get('logs', []))}")
            elif status == "0x1" and not has_input and value_wei >= LARGE_VALUE_WEI:
                plain_candidates.append((value_wei, mk(
                    t, r, "plain_transfer", checked_at,
                    value=wei_str(t["value"]),
                    value_basis="tx value field, raw wei",
                    extra_notes=f"Large-value plain transfer: {wei_str(t['value'])} wei. Zero-value plain transfers already covered by frozen t01.")))
                print(f"plain-large candidate: {h} block {int(r['blockNumber'], 16)} value={wei_str(t['value'])}")
            if filled():
                break

    plain_candidates.sort(key=lambda p: -p[0])
    plain = [tr for _, tr in plain_candidates[:2]]
    missing = []
    if len(found["token_transfer"]) < 2:
        missing.append("token_transfer")
    if len(found["contract_interaction"]) < 2:
        missing.append("contract_interaction")
    if reverted_value is None:
        missing.append("reverted_tx(with value)")
    if reverted_contract is None:
        missing.append("reverted_tx(contract)")
    if len(found["multi_recipient_tx"]) < 2:
        missing.append("multi_recipient_tx")
    if len(plain) < 2:
        missing.append("plain_transfer")
    if missing:
        print(f"FAILED to fill categories after scanning {scanned} blocks: {missing}")
        print({c: len(v) for c, v in found.items()},
              "reverted_value:", bool(reverted_value),
              "reverted_contract:", bool(reverted_contract),
              "plain_candidates:", len(plain_candidates))
        return 1

    # Order: t13-t14 token, t15-t16 contract, t17-t18 reverted,
    # t19-t20 multi, t21-t22 plain, t23-t24 unknown.
    ordered = (found["token_transfer"] + found["contract_interaction"]
               + [reverted_value, reverted_contract]
               + found["multi_recipient_tx"] + plain)
    traps = []
    for i, tr in enumerate(ordered):
        tr["trap_id"] = f"t{13 + i:02d}-{tr['category'].replace('_', '-')}"
        traps.append(tr)

    # unknown_tx x2: random hashes verified absent (no tx, no receipt).
    for n in (23, 24):
        for _ in range(20):
            cand = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(64))
            if any(cand == tr["tx_hash"] for tr in traps):
                continue
            tx_u, rec_u = rpc_batch([("eth_getTransactionByHash", [cand]),
                                     ("eth_getTransactionReceipt", [cand])])
            if tx_u is None and rec_u is None:
                traps.append({
                    "trap_id": f"t{n:02d}-unknown-tx",
                    "category": "unknown_tx",
                    "intent": INTENT,
                    "tx_hash": cand,
                    "expected_status": "not_found",
                    "expected_from": None,
                    "expected_to": None,
                    "expected_value": None,
                    "expected_block": None,
                    "value_basis": None,
                    "strict_unknown": True,
                    "provenance": {
                        "source": "Base Sepolia public RPC",
                        "source_url": "https://base-sepolia-rpc.publicnode.com",
                        "block": None,
                        "checked_at": checked_at,
                        "checker": "freeze script (curl JSON-RPC), 9 Nov 2026",
                        "notes": "Random well-formed hash; eth_getTransactionByHash and eth_getTransactionReceipt both returned null at freeze time. Scoring v2 (strict_unknown): a not_found answer carrying any invented from/to/value/block fails outright. If this hash ever appears on chain, retire the trap — do not re-score it.",
                    },
                })
                print(f"unknown: {cand}")
                break
        else:
            print(f"FAILED: could not find absent hash for t{n:02d}")
            return 1

    doc = {
        "data_kind": "FROZEN_TRAPS",
        "freeze_time_utc": checked_at,
        "intent": INTENT,
        "chain": "base-sepolia",
        "scoring_version": "v2 (this set only)",
        "scoring_semantics": (
            "Expansion set, 9 Nov 2026 — ADDITIVE to the frozen 12, which are "
            "unchanged. Differences from the frozen-12 semantics, disclosed: "
            "(1) token_transfer traps score the NATIVE tx value field (raw wei), "
            "not the Transfer-event amount; a native value of 0 is scored as "
            "\"0\" explicitly. (2) unknown_tx traps carry strict_unknown=true: "
            "a not_found answer with any invented from/to/value/block fails "
            "outright (scoring v2). (3) contract_interaction value and "
            "multi_recipient recipient lists remain unscored, stated per trap. "
            "Field-weighted accuracy is published as a co-primary metric "
            "alongside pass rate for this set. The frozen 12 keep their "
            "original semantics and scoring; combined 24-trap numbers are "
            "never presented as one uniform measure."
        ),
        "freeze_notes": (
            "Frozen 9 Nov 2026, immediately before the first scored purchase "
            "against this set. Additive expansion of the frozen 12 "
            "(traps-frozen-2026-11-06.json, untouched): 2 traps per category, "
            "t13-t24. Ground truth verified against Base Sepolia public RPC "
            "at freeze time; see per-trap provenance."
        ),
        "traps": traps,
    }
    OUT.write_text(json.dumps(doc, indent=2))
    print(f"wrote {OUT} with {len(traps)} traps")
    for tr in traps:
        print(f"  {tr['trap_id']} {tr['category']} {tr['tx_hash'][:18]}... "
              f"status={tr['expected_status']} block={tr['expected_block']} "
              f"value={tr['expected_value']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
