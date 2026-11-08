"""Freeze the 12-trap set for the 6 Nov 2026 full scored run.

Scans recent Base Sepolia blocks via curl-backed JSON-RPC (publicnode),
classifies transactions into the six categories (2 each), verifies ground
truth from tx + receipt data, and writes traps-frozen-2026-11-06.json.
Run once, before any scored purchase in this run. Never re-run after
scoring starts.
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
OUT = Path(__file__).resolve().parent.parent / "traps-frozen-2026-11-06.json"


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


def main():
    checked_at = now_iso()
    latest = int(rpc("eth_blockNumber", []), 16)
    print(f"latest base sepolia block: {latest} (checked {checked_at})")

    # Reuse t01 as one plain-transfer trap; verify its ground truth live.
    t01_hash = "0xd47a090fee50ae43d3af7dcb03eced0be6c98a48b3aa92dc21a8c4d9d784ae96"
    tx, rec = rpc_batch([("eth_getTransactionByHash", [t01_hash]),
                         ("eth_getTransactionReceipt", [t01_hash])])
    assert tx and rec, "t01 no longer retrievable"
    assert int(rec["blockNumber"], 16) == 53047427, "t01 block moved?!"
    assert rec["status"] == "0x1"
    t01 = {
        "trap_id": "t01-plain-transfer",
        "category": "plain_transfer",
        "intent": INTENT,
        "tx_hash": t01_hash,
        "expected_status": "confirmed",
        "expected_from": tx["from"],
        "expected_to": tx["to"],
        "expected_value": wei_str(tx["value"]),
        "expected_block": 53047427,
        "value_basis": "tx value field, raw wei",
        "provenance": {
            "source": "Base Sepolia public RPC",
            "source_url": "https://base-sepolia-rpc.publicnode.com",
            "block": 53047427,
            "checked_at": checked_at,
            "checker": "freeze script (curl JSON-RPC), 6 Nov 2026",
            "notes": "Reused from 1 Nov candidate notes; ground truth re-verified live at freeze. Pre-freeze smoke test trap (test-purchase-1, TxLens, FAIL).",
        },
    }
    print(f"t01 verified: from={tx['from']} to={tx['to']} value={tx['value']}")

    # Token candidate from 1 Nov notes; verify live.
    tok_hash = "0x0113bafdf54755989384d25240447e2071e4888da16686d180cc4eacc846b9af"
    tx2, rec2 = rpc_batch([("eth_getTransactionByHash", [tok_hash]),
                           ("eth_getTransactionReceipt", [tok_hash])])
    assert tx2 and rec2 and rec2["status"] == "0x1"
    transfers = [l for l in rec2["logs"]
                 if l["topics"] and l["topics"][0].lower() == TRANSFER_TOPIC]
    assert transfers, "token candidate has no Transfer event"
    first = transfers[0]
    tok = {
        "trap_id": "t02-token-transfer",
        "category": "token_transfer",
        "intent": INTENT,
        "tx_hash": tok_hash,
        "expected_status": "confirmed",
        "expected_from": tx2["from"],
        "expected_to": tx2["to"],
        "expected_value": str(int(first["data"], 16)),
        "expected_block": int(rec2["blockNumber"], 16),
        "value_basis": "Transfer event amount, raw token units",
        "token_contract": first["address"],
        "provenance": {
            "source": "Base Sepolia public RPC",
            "source_url": "https://base-sepolia-rpc.publicnode.com",
            "block": int(rec2["blockNumber"], 16),
            "checked_at": checked_at,
            "checker": "freeze script (curl JSON-RPC), 6 Nov 2026",
            "notes": f"Reused from 1 Nov candidate notes; re-verified live. Transfer events in receipt: {len(transfers)}. Token contract {first['address']}; value is the first Transfer event amount (tx value field is {wei_str(tx2['value'])} wei, NOT the scored value).",
        },
    }
    print(f"t02 verified: token={first['address']} event_amount={tok['expected_value']} block={tok['expected_block']}")

    found = {"plain_transfer": [t01], "token_transfer": [tok],
             "contract_interaction": [], "reverted_tx": [],
             "multi_recipient_tx": []}
    need = {"plain_transfer": 1, "token_transfer": 1,
            "contract_interaction": 2, "reverted_tx": 2,
            "multi_recipient_tx": 2}

    # Scan recent blocks backwards for the remaining categories.
    # Batch: one block fetch per block, then one batched receipt call.
    blk = latest
    scanned = 0
    while any(len(found[c]) < 2 for c in need) and scanned < 4000:
        block = rpc("eth_getBlockByNumber", [hex(blk), False])
        scanned += 1
        if block and block.get("transactions"):
            hashes = block["transactions"]
            receipts = rpc_batch([("eth_getTransactionReceipt", [h]) for h in hashes])
            txs = rpc_batch([("eth_getTransactionByHash", [h]) for h in hashes])
            for h, r, t in zip(hashes, receipts, txs):
                if not r or not t:
                    continue
                status = r["status"]
                transfers = [l for l in r.get("logs", [])
                             if l["topics"] and l["topics"][0].lower() == TRANSFER_TOPIC]
                inp = t.get("input") or "0x"
                has_input = inp not in ("0x", "", None) and len(inp) > 2
                if status == "0x0" and len(found["reverted_tx"]) < 2:
                    found["reverted_tx"].append(mk(t, r, "reverted_tx", "t",
                        checked_at, extra_notes="Receipt status 0x0."))
                    print(f"reverted: {h} block {int(r['blockNumber'],16)}")
                elif status == "0x1" and len(transfers) >= 2 and len(found["multi_recipient_tx"]) < 2:
                    recipients = {l["topics"][2].lower() for l in transfers
                                  if len(l["topics"]) > 2}
                    if len(recipients) >= 2:
                        found["multi_recipient_tx"].append(mk(t, r, "multi_recipient_tx", "t",
                            checked_at, extra_notes=f"{len(transfers)} Transfer events in receipt to {len(recipients)} distinct recipients; recipient list is a note, not scored."))
                        print(f"multi: {h} block {int(r['blockNumber'],16)} transfers={len(transfers)} recipients={len(recipients)}")
                elif status == "0x1" and len(transfers) == 1 and len(found["token_transfer"]) < 2 \
                        and inp.startswith(("0xa9059cbb", "0x23b872dd")):
                    first = transfers[0]
                    tr = mk(t, r, "token_transfer", "t", checked_at,
                            value=str(int(first["data"], 16)),
                            value_basis="Transfer event amount, raw token units")
                    tr["token_contract"] = first["address"]
                    tr["provenance"]["notes"] += f" Token contract {first['address']}; tx value field is {wei_str(t['value'])} wei, NOT the scored value."
                    found["token_transfer"].append(tr)
                    print(f"token: {h} block {int(r['blockNumber'],16)}")
                elif status == "0x1" and not has_input and len(found["plain_transfer"]) < 2:
                    # plain native transfer: empty input, value > 0 preferred
                    if int(t["value"], 16) > 0:
                        found["plain_transfer"].append(mk(t, r, "plain_transfer", "t", checked_at))
                        print(f"plain: {h} block {int(r['blockNumber'],16)} value={wei_str(t['value'])}")
                elif status == "0x1" and has_input and not transfers and len(found["contract_interaction"]) < 2:
                    code = rpc("eth_getCode", [t["to"], "latest"])
                    if code and code != "0x":
                        found["contract_interaction"].append(mk(t, r, "contract_interaction", "t",
                            checked_at, extra_notes="Non-empty input to a contract (code present at `to`); no Transfer events in receipt; tx value scored only if non-zero."))
                        print(f"contract: {h} block {int(r['blockNumber'],16)} to={t['to']}")
                if all(len(found[c]) >= 2 for c in need):
                    break
        blk -= 1

    missing = [c for c in need if len(found[c]) < 2]
    if missing:
        print(f"FAILED to fill categories after scanning {scanned} blocks: {missing}")
        print({c: len(found[c]) for c in found})
        return 1

    # Assign trap ids in category order.
    order = ["plain_transfer", "token_transfer", "contract_interaction",
             "reverted_tx", "multi_recipient_tx"]
    traps = []
    n = 0
    for cat in order:
        for tr in found[cat]:
            n += 1
            tr["trap_id"] = f"t{n:02d}-{cat.replace('_', '-')}"
            traps.append(tr)

    # unknown_tx: random hash verified absent (no tx, no receipt).
    for _ in range(20):
        cand = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(64))
        tx_u, rec_u = rpc_batch([("eth_getTransactionByHash", [cand]),
                                 ("eth_getTransactionReceipt", [cand])])
        if tx_u is None and rec_u is None:
            traps.append({
                "trap_id": "t12-unknown-tx",
                "category": "unknown_tx",
                "intent": INTENT,
                "tx_hash": cand,
                "expected_status": "not_found",
                "expected_from": None,
                "expected_to": None,
                "expected_value": None,
                "expected_block": None,
                "value_basis": None,
                "provenance": {
                    "source": "Base Sepolia public RPC",
                    "source_url": "https://base-sepolia-rpc.publicnode.com",
                    "block": None,
                    "checked_at": checked_at,
                    "checker": "freeze script (curl JSON-RPC), 6 Nov 2026",
                    "notes": "Random well-formed hash; eth_getTransactionByHash and eth_getTransactionReceipt both returned null at freeze time. If this hash ever appears on chain, retire the trap — do not re-score it.",
                },
            })
            print(f"unknown: {cand}")
            break
    else:
        print("FAILED: could not find an absent hash (extremely unlikely)")
        return 1

    # Second unknown trap (t11) — same procedure.
    for _ in range(20):
        cand = "0x" + "".join(random.choice("0123456789abcdef") for _ in range(64))
        if cand == traps[-1]["tx_hash"]:
            continue
        tx_u, rec_u = rpc_batch([("eth_getTransactionByHash", [cand]),
                                 ("eth_getTransactionReceipt", [cand])])
        if tx_u is None and rec_u is None:
            traps.insert(11, {
                "trap_id": "t11-unknown-tx",
                "category": "unknown_tx",
                "intent": INTENT,
                "tx_hash": cand,
                "expected_status": "not_found",
                "expected_from": None,
                "expected_to": None,
                "expected_value": None,
                "expected_block": None,
                "value_basis": None,
                "provenance": {
                    "source": "Base Sepolia public RPC",
                    "source_url": "https://base-sepolia-rpc.publicnode.com",
                    "block": None,
                    "checked_at": checked_at,
                    "checker": "freeze script (curl JSON-RPC), 6 Nov 2026",
                    "notes": "Random well-formed hash; eth_getTransactionByHash and eth_getTransactionReceipt both returned null at freeze time. If this hash ever appears on chain, retire the trap — do not re-score it.",
                },
            })
            print(f"unknown: {cand}")
            break
    else:
        print("FAILED: second unknown hash not found")
        return 1

    # Renumber: t01..t10 mined categories in order, t11/t12 unknown.
    for i, tr in enumerate(traps):
        cat = tr["category"].replace("_", "-")
        tr["trap_id"] = f"t{i+1:02d}-{cat}"

    doc = {
        "data_kind": "FROZEN_TRAPS",
        "freeze_time_utc": checked_at,
        "intent": INTENT,
        "chain": "base-sepolia",
        "freeze_notes": (
            "Frozen 6 Nov 2026, immediately before the first scored purchase of the "
            "full run. This set must not change after the first scored purchase in "
            "this run. Pre-freeze smoke test (NOT part of this run): test-purchase-1, "
            "TxLens 9002, trap t01, answered not_found for a confirmed tx, scored "
            "FAIL, saved in results-live/test-purchase-1.json (data_kind LIVE). "
            "Ground truth verified against Base Sepolia public RPC at freeze time; "
            "see per-trap provenance. Value basis per trap_design.md: plain = tx "
            "value (wei); token = Transfer event amount (raw token units); "
            "contract/reverted/multi = tx value only when non-zero, else unscored."
        ),
        "traps": traps,
    }
    OUT.write_text(json.dumps(doc, indent=2))
    print(f"wrote {OUT} with {len(traps)} traps")
    for tr in traps:
        print(f"  {tr['trap_id']} {tr['category']} {tr['tx_hash'][:18]}... "
              f"status={tr['expected_status']} block={tr['expected_block']}")
    return 0


def mk(t, r, category, _prefix, checked_at, value=None, value_basis=None,
       extra_notes=""):
    """Build a trap record from live tx + receipt dicts."""
    status = "reverted" if r["status"] == "0x0" else "confirmed"
    v = value
    if v is None:
        v = wei_str(t["value"]) if int(t["value"], 16) > 0 else None
    basis = value_basis or ("tx value field, raw wei" if v is not None else None)
    return {
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
            "checker": "freeze script (curl JSON-RPC), 6 Nov 2026",
            "notes": extra_notes,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
