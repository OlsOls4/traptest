"""Second-provider mini-run: 12 frozen traps x ONE more provider (6 Nov 2026).

DEPRECATED (Council F5, 9 Nov 2026) — do not use for new runs. The
supported replay path is the parametrised runner:
`python3 -m traptest.run --traps ... --providers ... --out ...`
(see docs/how-to-run.md §3), which resolves providers against a fresh
catalogue fetch and refuses an absent miner instead of trying a
hardcoded candidate list. This script is kept only so the historical
6 Nov 2026 mini-run stays re-runnable in exactly its original shape,
to a new file. Its hardcoded 12-trap set and candidate list
(Sigil 9010, OnChain Intel 900, Truvian 8453) are retired and must not
be copied into new tooling.

Tries candidates in order from a FRESH catalogue re-fetch at run time:
Sigil (9010), then OnChain Intel (900), then Truvian (8453). A candidate
is skipped if absent from the catalogue; a candidate that answers
503/no_compatible_miner on ALL 12 traps is recorded as unservable and the
next candidate is tried. A provider that serves answers — even if every
trap scores FAIL — is a real result and the run stops there.

HISTORICAL SCRIPT — the 6 Nov 2026 mini-run is DONE (Truvian 8453
served 3/12; the 60-row file is FROZEN). This script reads that frozen
file as its starting doc (read-only) and writes the updated doc ONLY
to a NEW --out file; it refuses to overwrite the frozen results
files (results-live/full-run-2026-11-06.json, results-live/results.json,
docs/leaderboard/results.json). The leaderboard-view JSONs are written
next to --out instead. The parametrised replay path for a judge is
`python3 -m traptest.run --traps ... --providers ... --out ...`
(see docs/how-to-run.md §3).

Cost: 12 calls x $0.01 = $0.12 testnet max for this run. Session total
($0.12 full run + $0.02 smoke tests + this run) must stay under $0.50.
One attempt per trap+miner, except a single retry when the failure was a
transport-level error before any payment was attempted.

Shared harness: transport, Sepolia RPC, balances, fail_row (which
records escrow_credit_usd at write time), scored-row building and
receipt verification all live in traptest/harness.py (Council finding
F-dup — the copies that used to live here are deleted). The old
post-hoc "Repair the run-1 record" mutation of historical Sigil rows
is deleted with them: the 6 Nov file already carries the corrected
escrow values, and a runner must never rewrite history.

Run: python3 scripts/mini_run.py --out results-live/mini-replay-<date>.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from traptest.harness import (  # noqa: E402
    BURNER, MissingKeyError, build_scored_row, curl_transport,
    eth_balance, fail_row, read_key_file, token_balance, verify_receipts)
from traptest.providers import (  # noqa: E402
    DirectAskClient, TransportHTTPError, PurchaseFailedError,
    PaymentRequiredError, UnknownMinerError)
from traptest.traps import Trap  # noqa: E402
from traptest.x402 import make_x402_provider  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
CANDIDATES = [("9010", "Sigil"), ("900", "OnChain Intel"), ("8453", "Truvian")]
RUN_CAP_USD = 0.12          # this mini-run only
SESSION_CAP_USD = 0.50      # full session: full run $0.12 + smoke $0.02 + this run
PRIOR_SPEND_USD = 0.14
HISTORICAL = ROOT / "results-live" / "full-run-2026-11-06.json"
FROZEN_FILES = (
    ROOT / "results-live" / "full-run-2026-11-06.json",
    ROOT / "results-live" / "results.json",
    ROOT / "docs" / "leaderboard" / "results.json",
)


def main():
    parser = argparse.ArgumentParser(
        description="Historical mini-run (6 Nov 2026 shape) — writes only to a NEW --out file")
    parser.add_argument("--out", required=True,
                        help="output results path (must NOT exist; the frozen "
                        "results files are never overwritten)")
    args = parser.parse_args()
    print("DEPRECATED: scripts/mini_run.py is retired (Council F5). For new "
          "runs use: python3 -m traptest.run --traps <trap-set.json> "
          "--providers <id[,id...]> --out <new file>. This script keeps "
          "only its historical 12-trap shape and candidate list.",
          file=sys.stderr)
    out = Path(args.out)
    if any(out.resolve() == f.resolve() for f in FROZEN_FILES):
        print(f"REFUSED: --out is a frozen results file ({out}). "
              "Point --out at a new file.", file=sys.stderr)
        return 6
    if out.exists():
        print(f"REFUSED: --out already exists: {out}. The runner is "
              "append-only; point --out at a new file.", file=sys.stderr)
        return 6

    frozen = json.loads((ROOT / "traps-frozen-2026-11-06.json").read_text())
    traps_raw = frozen["traps"]
    assert len(traps_raw) == 12
    traps = [Trap(trap_id=t["trap_id"], intent=t["intent"], tx_hash=t["tx_hash"],
                  expected_status=t["expected_status"], expected_from=t["expected_from"],
                  expected_to=t["expected_to"], expected_value=t["expected_value"],
                  expected_block=t["expected_block"]) for t in traps_raw]
    by_id = {t["trap_id"]: t for t in traps_raw}

    doc = json.loads(HISTORICAL.read_text())
    assert doc["data_kind"] == "LIVE"
    # Continuation-safe: the first mini-run attempt (Sigil) may already be
    # recorded. Never re-buy a provider already in scores.
    assert len(doc["scores"]) >= 24, f"expected >=24 existing rows, got {len(doc['scores'])}"
    existing_providers = {r["provider_id"] for r in doc["scores"]}
    assert PRIOR_SPEND_USD + RUN_CAP_USD <= SESSION_CAP_USD
    prior_mini = doc.get("mini_run") or {}
    prior_attempts = list(prior_mini.get("attempts") or [])
    # Out-of-wallet so far (billed + escrow-credited) is the real cap basis:
    # recompute from the recorded balance drop, not from cost_usd alone.
    out_of_wallet = round(doc["burner3_balance_before_usdc"]
                          - doc.get("burner3_balance_after_usdc",
                                    doc["burner3_balance_before_usdc"]), 4)
    print(f"out-of-wallet so far (balance drop): ${out_of_wallet:.2f} "
          f"(billed ${doc['total_cost_usd']:.2f} + escrow "
          f"${out_of_wallet - doc['total_cost_usd']:.2f})")

    try:
        key = read_key_file(ROOT / ".burner3.key")
    except MissingKeyError as e:
        print(str(e), file=sys.stderr)
        return 4
    provider = make_x402_provider(key, validity_seconds=55)
    client = DirectAskClient(transport=curl_transport, payment_provider=provider)

    bal_before = token_balance(BURNER)
    eth_before = eth_balance(BURNER)
    print(f"burner3 before mini-run: {bal_before} test USDC, {eth_before} Sepolia ETH")

    miners = client.miners(INTENT)
    by_mid = {}
    for entry in miners:
        if isinstance(entry, dict):
            mid = entry.get("id") or entry.get("miner_id") or entry.get("minerId")
            if mid is not None:
                by_mid[str(mid)] = entry
    print(f"{len(by_mid)} live miners in fresh catalogue: {sorted(by_mid)}")

    spent = 0.0
    chosen = None
    attempts = list(prior_attempts)
    unservable_rows = []  # real failed calls (cost 0), kept in scores like LiveCert's
    escrow_this_run = 0.0  # settled into escrow credit during THIS run (not billed)

    for mid, name in CANDIDATES:
        if mid in existing_providers:
            print(f"{name} ({mid}) already ran — skipping (rows kept)")
            continue
        # Stop before a candidate if even a full 12-call drain would take
        # out-of-wallet spend to the $0.50 session cap.
        if out_of_wallet + escrow_this_run + spent + 0.12 >= SESSION_CAP_USD:
            print(f"CAP: not trying {name} ({mid}) — would reach "
                  f"${out_of_wallet + escrow_this_run + spent + 0.12:.2f} out-of-wallet")
            attempts.append({"provider_id": mid, "name": name,
                             "outcome": "not_attempted_session_cap",
                             "reason": "would reach $0.50 session cap"})
            continue
        if mid not in by_mid:
            print(f"{name} ({mid}) ABSENT from fresh catalogue — skipping")
            attempts.append({"provider_id": mid, "name": name,
                             "outcome": "absent_from_catalogue"})
            continue
        print(f"Trying {name} ({mid}) — {by_mid[mid].get('name')}")
        bal_c = token_balance(BURNER)
        spent_c = spent
        rows = []
        served = 0
        unservable_503 = 0
        for trap in traps:
            label = f"{trap.trap_id} x {mid}"
            if spent + 0.01 > RUN_CAP_USD:
                print(f"CAP: stopping before {label} (spent {spent})")
                rows.append({**fail_row(trap, mid, "spend cap reached, not attempted"),
                             "skipped_cap": True})
                continue
            try:
                result = client.buy_result(INTENT, mid,
                                           {"tx_hash": trap.tx_hash, "chain": "base-sepolia"})
            except (TransportHTTPError, PurchaseFailedError, PaymentRequiredError,
                    UnknownMinerError) as e:
                retryable = isinstance(e, TransportHTTPError) and e.response.status == 0
                if retryable:
                    print(f"{label}: transport failure pre-payment, one retry")
                    try:
                        result = client.buy_result(INTENT, mid, {"tx_hash": trap.tx_hash,
                                                                 "chain": "base-sepolia"})
                    except Exception as e2:
                        print(f"{label}: FAILED after retry: {type(e2).__name__}: {str(e2)[:200]}")
                        rows.append(fail_row(trap, mid, f"{type(e2).__name__}: {str(e2)[:300]}"))
                        if isinstance(e2, PurchaseFailedError) and "503" in str(e2):
                            unservable_503 += 1
                        continue
                else:
                    print(f"{label}: FAILED: {type(e).__name__}: {str(e)[:200]} "
                          f"(a failed call may still have settled $0.01 "
                          f"into escrow credit — never assumed $0)")
                    rows.append(fail_row(trap, mid, f"{type(e).__name__}: {str(e)[:300]}"))
                    if isinstance(e, PurchaseFailedError) and "503" in str(e):
                        unservable_503 += 1
                    continue
            served += 1
            if result.charged:
                spent += float(result.cost_usd or 0)
            row = build_scored_row(trap, by_id[trap.trap_id], mid, INTENT, result)
            print(f"{label}: charged={result.charged} cost={result.cost_usd} "
                  f"passed={row['passed']} status={row['normalised_answer'].get('status')!r} "
                  f"norm={row['normalisation_notes']}")
            rows.append(row)
        # Balance check per candidate: money that left the wallet without
        # being billed is escrow credit, and it counts against the cap.
        drained_c = round((bal_c - token_balance(BURNER)) - (spent - spent_c), 4)
        if drained_c:
            print(f"{name} ({mid}): ${drained_c:.2f} settled into escrow credit (not billed)")
            escrow_this_run = round(escrow_this_run + drained_c, 4)
        passed = sum(1 for r in rows if r.get("passed"))
        # Unservable = NO answer served on any trap, whatever the error
        # shape (LiveCert: 503/no_compatible_miner; Sigil: 500 upstream
        # 404). A provider that serves answers — even all FAIL — is a
        # real result and the run stops there.
        if served == 0:
            err_kinds = sorted({(r.get("error") or "").split(":")[0] for r in rows})
            print(f"{name} ({mid}): UNSERVABLE — 0/12 served "
                  f"(errors: {err_kinds}), ${spent:.2f} billed")
            unservable_rows.extend(rows)
            attempts.append({"provider_id": mid, "name": name,
                             "outcome": "unservable_0_of_12_served",
                             "error_kinds": err_kinds,
                             "cost_usd": 0, "rows": rows})
            continue
        print(f"{name} ({mid}): SERVED {served}/12, {passed}/12 passed, spent ${spent:.2f}")
        chosen = (mid, name, rows, passed)
        attempts.append({"provider_id": mid, "name": name,
                         "outcome": "served", "passed": passed,
                         "served": served, "cost_usd": round(spent, 4)})
        break

    # Verify settlement receipts on-chain for any new served rows.
    new_rows = chosen[2] if chosen else []
    verified, total = verify_receipts(new_rows)
    if total:
        print(f"receipts verified on-chain: {verified}/{total} settled")

    bal_after = token_balance(BURNER)
    eth_after = eth_balance(BURNER)

    new_rows_all = list(unservable_rows) + (chosen[2] if chosen else [])
    escrow_credit = round(sum(float(r.get("escrow_credit_usd") or 0)
                              for r in new_rows_all), 4)
    prior_escrow = round(out_of_wallet - doc["total_cost_usd"], 4)

    if chosen:
        mid, name, rows, passed = chosen
        doc["scores"].extend(unservable_rows)
        doc["scores"].extend(rows)
        doc["providers"]["mini_run_slot"] = mid
        doc["mini_run"] = {"provider_id": mid, "name": name, "passed": passed,
                           "traps_run": len(rows), "cost_usd": round(spent, 4),
                           "attempts": attempts}
    else:
        # No provider served this run: keep the PRIOR served mini_run
        # record (e.g. Truvian 8453, 3/12) intact — a re-run that finds
        # nothing new must not overwrite it with "no second provider
        # could serve the intent". Only the attempts log grows.
        doc["scores"].extend(unservable_rows)
        if prior_mini.get("provider_id"):
            doc["mini_run"] = {**prior_mini, "attempts": attempts}
        else:
            doc["mini_run"] = {"provider_id": None, "passed": 0, "traps_run": 0,
                               "cost_usd": 0, "attempts": attempts,
                               "outcome": "no second provider could serve the intent"}
    doc["total_cost_usd"] = round(doc["total_cost_usd"] + spent, 4)
    doc["escrow_credit_usd"] = round(prior_escrow + escrow_credit, 4)
    doc["burner3_balance_after_usdc"] = bal_after
    doc["burner3_eth_after"] = eth_after
    doc["balance_drop_usdc"] = round(doc["burner3_balance_before_usdc"] - bal_after, 4)
    out.write_text(json.dumps(doc, indent=2))

    # Regenerate the leaderboard views from the same rows — next to
    # --out, never over the frozen results.json / leaderboard files.
    n_providers = len({r["provider_id"] for r in doc["scores"]})
    results = {
        "data_kind": "LIVE",
        "intent": INTENT,
        "generated_for": (f"Live leaderboard for the 6 Nov 2026 full scored run "
                          f"(12 frozen traps x {n_providers} providers, event window "
                          f"1 Nov-1 Dec 2026). Every row is a real Telegraph Direct Ask "
                          f"purchase (or a real failed call, cost 0) with a real "
                          f"receipt/signal."),
        "run": "full-run-2026-11-06",
        "freeze_time_utc": frozen["freeze_time_utc"],
        "traps_file": "traps-frozen-2026-11-06.json",
        "total_cost_usd": doc["total_cost_usd"],
        "escrow_credit_usd": doc.get("escrow_credit_usd", 0),
        "burner3_balance_before_usdc": doc["burner3_balance_before_usdc"],
        "burner3_balance_after_usdc": bal_after,
        "scores": doc["scores"],
    }
    results_view = out.with_name(out.stem + ".results.json")
    leaderboard_view = out.with_name(out.stem + ".leaderboard.json")
    results_view.write_text(json.dumps(results, indent=2))
    leaderboard_view.write_text(json.dumps(results, indent=2))

    print(f"DONE: {len(doc['scores'])} rows total, mini-run billed ${spent:.2f}, "
          f"escrow-credited ${escrow_credit:.2f}, "
          f"session billed ${doc['total_cost_usd']:.2f}, "
          f"session out-of-wallet ${doc['total_cost_usd'] + doc.get('escrow_credit_usd', 0):.2f}, "
          f"balance {bal_before} -> {bal_after} USDC (drop {bal_before - bal_after:.2f}), "
          f"ETH {eth_before} -> {eth_after}")
    print(f"  wrote {out}, {results_view}, {leaderboard_view}")
    if chosen:
        print(f"  {chosen[1]} ({chosen[0]}): {chosen[3]}/12 passed")
    else:
        print("  NO second provider could serve the intent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
