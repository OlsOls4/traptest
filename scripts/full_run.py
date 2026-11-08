"""Full scored run: 12 frozen traps x 2 providers (6 Nov 2026, event window).

Reads the FROZEN trap set (traps-frozen-2026-11-06.json) — never edits it —
buys each trap from TxLens (9002) and LiveCert (4433) via Direct Ask with
the x402 provider on burner 3, scores with traptest/scoring.py, and writes
the results incrementally (data_kind LIVE).

HISTORICAL SCRIPT — the 6 Nov 2026 run is DONE and its results file
(results-live/full-run-2026-11-06.json, 60 rows) is FROZEN. This script
no longer writes to it: it refuses to run without --out pointing at a
NEW file, and refuses an --out that already exists. The parametrised
replay path for a judge is `python3 -m traptest.run --traps ... \
--providers ... --out ...` (see docs/how-to-run.md §3); this script is
kept only so the historical run stays re-runnable in exactly its
original shape, to a new file.

Cost: 24 calls x $0.01 = $0.24 testnet max. HARD CAP $0.30 total for this
run: no buy is attempted once spent + $0.01 would exceed the cap.
One attempt per trap+miner, except a single retry when the failure was a
transport-level error before any payment was attempted (a failure after
payment is never retried — and a failed call may still settle $0.01
into Telegraph escrow credit, observed 6 Nov 2026, so a failed call is
never assumed to cost $0).

Answer normalisation (per trap_design.md §6, run-harness duty): providers
return `block_number` / `value_eth`; the scorer reads `block` / `value`.
Mapping is recorded per row and the RAW answer is always kept alongside
the normalised one, so every score is auditable. Normalisation is the
shared implementation in traptest/normalise.py (Decimal ETH -> wei,
including scientific notation such as "1e-05" and hex values); an
integer value_eth is ETH, not wei. For token traps the scored value is
the Transfer EVENT amount; a provider returning the tx value field (0)
scores wrong, correctly.

Shared harness: transport, Sepolia RPC, balances, fail_row, scored-row
building and receipt verification all live in traptest/harness.py
(Council finding F-dup — the copies that used to live here are deleted).

Run: python3 scripts/full_run.py --out results-live/replay-<date>.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from traptest.harness import (  # noqa: E402
    BURNER, MissingKeyError, build_scored_row, curl_transport,
    eth_balance, fail_row, read_key_file, sha256_file, token_balance,
    verify_receipts)
from traptest.providers import (  # noqa: E402
    DirectAskClient, TransportHTTPError, PurchaseFailedError,
    PaymentRequiredError, UnknownMinerError)
from traptest.traps import Trap  # noqa: E402
from traptest.x402 import make_x402_provider  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
PREFERRED = ["9002", "4433", "9010", "900", "9001", "8453", "20260828",
             "9007", "7307"]
SECONDARY = ["9010", "900", "9001", "8453", "20260828", "9007", "7307"]
SPEND_CAP_USD = 0.30
FROZEN_OUT = ROOT / "results-live" / "full-run-2026-11-06.json"


def main():
    parser = argparse.ArgumentParser(
        description="Historical full run (6 Nov 2026 shape) — writes only to a NEW --out file")
    parser.add_argument("--out", required=True,
                        help="output results path (must NOT exist; the frozen "
                        "results file is never overwritten)")
    args = parser.parse_args()
    out = Path(args.out)
    if out.resolve() == FROZEN_OUT.resolve():
        print(f"REFUSED: --out is the frozen 6 Nov 2026 results file "
              f"({FROZEN_OUT}). Point --out at a new file.", file=sys.stderr)
        return 6
    if out.exists():
        print(f"REFUSED: --out already exists: {out}. The runner is "
              "append-only; point --out at a new file.", file=sys.stderr)
        return 6

    frozen, traps_raw, traps_sha256 = _load_frozen()
    by_id = {t["trap_id"]: t for t in traps_raw}
    traps = [Trap(trap_id=t["trap_id"], intent=t["intent"], tx_hash=t["tx_hash"],
                  expected_status=t["expected_status"], expected_from=t["expected_from"],
                  expected_to=t["expected_to"], expected_value=t["expected_value"],
                  expected_block=t["expected_block"]) for t in traps_raw]

    try:
        key = read_key_file(ROOT / ".burner3.key")
    except MissingKeyError as e:
        print(str(e), file=sys.stderr)
        return 4
    provider = make_x402_provider(key, validity_seconds=55)
    client = DirectAskClient(transport=curl_transport, payment_provider=provider)

    bal_before = token_balance(BURNER)
    eth_before = eth_balance(BURNER)
    print(f"burner3 before: {bal_before} test USDC, {eth_before} Sepolia ETH")

    miners = client.miners(INTENT)
    by_mid = {}
    for entry in miners:
        if isinstance(entry, dict):
            mid = entry.get("id") or entry.get("miner_id") or entry.get("minerId")
            if mid is not None:
                by_mid[str(mid)] = entry
    print(f"{len(by_mid)} live miners: {sorted(by_mid)}")
    chosen = {}
    substitutions = []
    for want in ("9002", "4433"):
        if want in by_mid:
            chosen[want] = want
        else:
            alt = next((m for m in SECONDARY if m in by_mid), None)
            if alt is None:
                print(f"miner {want} absent and no substitute available")
                return 2
            chosen[want] = alt
            substitutions.append({"wanted": want, "used": alt,
                                  "reason": f"miner {want} absent from fresh catalogue"})
            print(f"SUBSTITUTION: {want} absent -> using {alt} ({by_mid[alt].get('name')})")
    provider_ids = [chosen["9002"], chosen["4433"]]
    print(f"providers: TxLens slot -> {provider_ids[0]}, LiveCert slot -> {provider_ids[1]}")

    rows = []
    spent = 0.0

    def save():
        out.write_text(json.dumps({
            "data_kind": "LIVE",
            "run": "full-run-2026-11-06",
            "intent": INTENT,
            "traps_file": "traps-frozen-2026-11-06.json",
            "traps_sha256": traps_sha256,
            "freeze_time_utc": frozen["freeze_time_utc"],
            "providers": {"txlens_slot": provider_ids[0], "livecert_slot": provider_ids[1]},
            "substitutions": substitutions,
            "spend_cap_usd": SPEND_CAP_USD,
            "total_cost_usd": round(spent, 4),
            "burner3_balance_before_usdc": bal_before,
            "burner3_eth_before": eth_before,
            "scores": rows,
        }, indent=2))

    def buy_once(trap, miner_id):
        return client.buy_result(INTENT, miner_id,
                                 {"tx_hash": trap.tx_hash, "chain": "base-sepolia"})

    for trap in traps:
        for miner_id in provider_ids:
            label = f"{trap.trap_id} x {miner_id}"
            if spent + 0.01 > SPEND_CAP_USD:
                print(f"CAP: stopping before {label} (spent {spent})")
                rows.append({**fail_row(trap, miner_id, "spend cap reached, not attempted"),
                             "skipped_cap": True})
                save()
                continue
            try:
                result = buy_once(trap, miner_id)
            except (TransportHTTPError, PurchaseFailedError, PaymentRequiredError,
                    UnknownMinerError) as e:
                # Single retry ONLY if nothing was paid: transport-level
                # failure on the first POST (status 0) with no 402 seen.
                retryable = isinstance(e, TransportHTTPError) and e.response.status == 0
                if retryable:
                    print(f"{label}: transport failure pre-payment, one retry")
                    try:
                        result = buy_once(trap, miner_id)
                    except Exception as e2:
                        print(f"{label}: FAILED after retry: {type(e2).__name__}: {str(e2)[:200]}")
                        rows.append(fail_row(trap, miner_id, f"{type(e2).__name__}: {str(e2)[:300]}"))
                        save()
                        continue
                else:
                    print(f"{label}: FAILED: {type(e).__name__}: {str(e)[:200]} "
                          f"(a failed call may still have settled $0.01 "
                          f"into escrow credit — never assumed $0)")
                    rows.append(fail_row(trap, miner_id, f"{type(e).__name__}: {str(e)[:300]}"))
                    save()
                    continue
            if result.charged:
                spent += float(result.cost_usd or 0)
            row = build_scored_row(trap, by_id[trap.trap_id], miner_id, INTENT, result)
            print(f"{label}: charged={result.charged} cost={result.cost_usd} "
                  f"passed={row['passed']} status={row['normalised_answer'].get('status')!r} "
                  f"norm={row['normalisation_notes']}")
            rows.append(row)
            save()

    # Verify settlement receipts on-chain (Sepolia) in one batch.
    verified, total = verify_receipts(rows)
    if total:
        print(f"receipts verified on-chain: {verified}/{total} settled")

    bal_after = token_balance(BURNER)
    eth_after = eth_balance(BURNER)
    doc = json.loads(out.read_text())
    doc["total_cost_usd"] = round(spent, 4)
    doc["burner3_balance_after_usdc"] = bal_after
    doc["burner3_eth_after"] = eth_after
    doc["balance_drop_usdc"] = round(bal_before - bal_after, 4)
    out.write_text(json.dumps(doc, indent=2))
    print(f"DONE: {len(rows)} rows, spent ${spent:.2f}, "
          f"balance {bal_before} -> {bal_after} USDC (drop {bal_before - bal_after:.2f}), "
          f"ETH {eth_before} -> {eth_after}")
    for mid in provider_ids:
        rs = [r for r in rows if r.get("provider_id") == mid and not r.get("skipped_cap")]
        p = sum(1 for r in rs if r.get("passed"))
        print(f"  {mid}: {p}/{len(rs)} passed")
    return 0


def _load_frozen():
    """Load + validate the frozen trap set; returns (doc, traps_raw, sha256)."""
    frozen_path = ROOT / "traps-frozen-2026-11-06.json"
    frozen = json.loads(frozen_path.read_text())
    traps_raw = frozen["traps"]
    assert len(traps_raw) == 12, f"frozen set must have 12 traps, has {len(traps_raw)}"
    assert len({t["trap_id"] for t in traps_raw}) == 12, "trap ids must be unique"
    cats = {}
    for t in traps_raw:
        cats[t["category"]] = cats.get(t["category"], 0) + 1
    assert all(cats.get(c, 0) == 2 for c in
               ("plain_transfer", "token_transfer", "contract_interaction",
                "reverted_tx", "multi_recipient_tx", "unknown_tx")), f"bad composition: {cats}"
    return frozen, traps_raw, sha256_file(frozen_path)


if __name__ == "__main__":
    raise SystemExit(main())
