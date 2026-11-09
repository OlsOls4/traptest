"""TrapTest live runner — GATED. Refuses any live purchase unless BOTH:

(a) the current UTC date is on/after 2026-11-01 (the Season II window), and
(b) an explicit activation marker file exists.

Default marker: <repo>/LIVE-ACTIVATED (override with --marker or the
TRAPTEST_ACTIVATION_MARKER env var). The marker is created by a human on
day 1 ONLY after the free-testnet gate passes (faucet claim landed in a
burner wallet at Telegraph's USDC contract) — creating it is NOT this
script's job and this script never creates wallets, claims faucets, or
holds keys.

This is the single parametrised replay path (Council rebuild, 8 Nov
2026). The old prep stub returned 3 with "payment provider not
configured in prep"; the x402 provider (traptest/x402.py, used live
6 Nov 2026) is now wired in, and the loop is:

    python3 -m traptest.run --traps <trap-set.json> \\
        --providers 9002,8453 --out results-live/replay-<date>.json

- --traps: trap-set JSON (event-window ground truth). Its sha256 is
  recorded in every output file; a trap set tuned after seeing
  answers invalidates the run.
- --providers: comma-separated miner IDs, resolved against a FRESH
  live catalogue fetch at run time — never trusted from a hardcoded
  list alone. A requested id absent from the catalogue is refused,
  never bought from a stale id. A re-run therefore scores whoever
  the catalogue returns for those ids on that day, which may differ
  from the 6 Nov 2026 run (miner ids are not stable).
- --out: output path. APPEND-ONLY: an existing file is refused
  (exit 6) unless --append is given; with --append, rows for
  (trap_id, provider_id) pairs already in the file are NOT re-bought
  and NOT duplicated — a second run with the same traps appends
  zero rows and spends zero. Appending a different trap set (sha256
  mismatch) is refused: different traps go in a new file.
- --dry-run: validates everything (gates, trap file, key file,
  provider resolution against the live catalogue, output path) and
  spends nothing, writes nothing, buys nothing.
- --spend-cap: hard cap in USD for this run (default $0.30); no buy
  is attempted once spent + $0.01 would exceed it. One attempt per
  trap+miner, except a single retry when the failure was a
  transport-level error before any payment was attempted (a failure
  after payment is never retried — and a failed call may still
  settle $0.01 into Telegraph escrow credit, observed 6 Nov 2026,
  so a failed call is never assumed to cost $0).

Key file: --key (default <repo>/.burner3.key). If it is absent the
runner exits 4 printing exact setup instructions and spends nothing
— never an unhandled FileNotFoundError. The key is read only to
sign; it is never written, logged, or committed.

Gate failure: prints GATE REFUSED to stderr and exits 2, having made
NO network call at all — the gate is checked before any client is
constructed. --list-miners (free discovery only, no purchase) needs
no key and no trap file.

Exit codes: 0 ok · 2 gate refused · 3 missing --traps/--providers ·
4 key file missing · 5 provider not in fresh catalogue ·
6 --out exists without --append · 7 trap-set mismatch on --append ·
8 post-loop receipt verification or balance read failed (rows already
saved; the output doc records receipt_verification_error /
balance_read_error).

Trap JSON format: {"traps": [{"trap_id","intent","tx_hash",
"expected_status","expected_from","expected_to","expected_value",
"expected_block", ...}]}. Ground truth must be checked against
public chain data in the event window before running — never
invented, never tuned to flatter a provider.
"""
import argparse
import json
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

WINDOW_OPEN = date(2026, 11, 1)
DEFAULT_MARKER = Path(__file__).resolve().parent.parent / "LIVE-ACTIVATED"
DEFAULT_KEY = Path(__file__).resolve().parent.parent / ".burner3.key"
DEFAULT_INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
DEFAULT_SPEND_CAP_USD = 0.30


def check_gates(today=None, marker=None):
    """Return (ok, reason). Pure: no network, no side effects."""
    today = today or datetime.now(timezone.utc).date()
    marker = Path(marker) if marker else DEFAULT_MARKER
    if today < WINDOW_OPEN:
        return False, (
            f"GATE REFUSED: today is {today.isoformat()} (UTC), before the "
            f"Season II window opens on {WINDOW_OPEN.isoformat()}. "
            "Live purchases are event-period only.")
    if not marker.exists():
        return False, (
            f"GATE REFUSED: activation marker missing: {marker}. "
            "Create it only on day 1 after the free-testnet gate passes "
            "(faucet claim confirmed in a burner wallet); it is not created "
            "automatically.")
    return True, f"gates passed: date {today.isoformat()}, marker {marker}"


def _new_run_id():
    return ("run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "-" + uuid.uuid4().hex[:6])


def main(argv=None, today=None, transport=None, payment_provider=None,
         balance_reader=None, receipt_verifier=None):
    """Run the loop. ``transport`` / ``payment_provider`` /
    ``balance_reader`` / ``receipt_verifier`` are injection points
    for tests (fake transport, no network, no spend); the live path
    passes none of them and uses curl + the x402 provider + Sepolia
    RPC. ``balance_reader(addr)`` returns (usdc, eth);
    ``receipt_verifier(rows)`` returns (verified, total)."""
    parser = argparse.ArgumentParser(
        description="TrapTest live runner (gated, parametrised)")
    parser.add_argument("--intent", default=DEFAULT_INTENT)
    parser.add_argument("--miner", help="miner id (deprecated alias for "
                        "--providers with a single id)")
    parser.add_argument("--providers",
                        help="comma-separated miner ids, resolved against "
                        "a fresh live catalogue fetch")
    parser.add_argument("--traps", help="path to trap-set JSON (event-window ground truth)")
    parser.add_argument("--out", help="output results path (new file; "
                        "--append to add to an existing one)")
    parser.add_argument("--append", action="store_true",
                        help="append to an existing --out file instead of "
                        "refusing it; already-scored (trap, provider) "
                        "pairs are not re-bought or duplicated")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate everything, spend nothing, write nothing")
    parser.add_argument("--spend-cap", type=float, default=DEFAULT_SPEND_CAP_USD,
                        help="hard spend cap in USD for this run (default 0.30)")
    parser.add_argument("--key", default=str(DEFAULT_KEY),
                        help="burner private-key file (default: ./.burner3.key)")
    parser.add_argument("--list-miners", action="store_true",
                        help="free discovery only: list live miners, no purchase")
    parser.add_argument("--marker", default=os.environ.get("TRAPTEST_ACTIVATION_MARKER"),
                        help="activation marker file (default: ./LIVE-ACTIVATED)")
    args = parser.parse_args(argv)

    ok, reason = check_gates(today=today, marker=args.marker)
    if not ok:
        print(reason, file=sys.stderr)
        return 2
    print(reason)

    # Network only happens from here on, and only free discovery unless
    # a payment provider is wired in below.
    try:
        from .harness import (  # package execution
            CALL_PRICE_USD, MissingKeyError, atomic_write_text,
            build_scored_row, curl_transport, eth_balance, fail_row,
            load_traps, read_key_file, token_balance, verify_receipts)
        from .providers import (  # noqa: F401  (re-exported for clarity)
            DirectAskClient, MAX_CALL_USD, PurchaseFailedError,
            PaymentRequiredError, TransportHTTPError, UnknownMinerError)
        from .x402 import make_x402_provider
    except ImportError:  # direct script execution: python traptest/run.py
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from traptest.harness import (  # noqa: F401
            CALL_PRICE_USD, MissingKeyError, atomic_write_text,
            build_scored_row, curl_transport, eth_balance, fail_row,
            load_traps, read_key_file, token_balance, verify_receipts)
        from traptest.providers import (  # noqa: F401
            DirectAskClient, MAX_CALL_USD, PurchaseFailedError,
            PaymentRequiredError, TransportHTTPError, UnknownMinerError)
        from traptest.x402 import make_x402_provider

    if balance_reader is None:
        def balance_reader(addr):
            return token_balance(addr), eth_balance(addr)
    if receipt_verifier is None:
        receipt_verifier = verify_receipts

    from .harness import BURNER  # noqa: E402  (single source of the burner address)

    if args.list_miners:
        # Default engine transport is curl (harness): urllib truncates
        # this server's chunked catalogue response on this VM
        # (IncompleteRead at ~16KB of a 28KB body, observed 8 Nov 2026),
        # while curl fetches it whole. Tests inject a fake transport.
        client = DirectAskClient(transport=transport or curl_transport)
        try:
            miners = client.miners(args.intent)
        except Exception as e:  # free GET, but the engine can be flaky
            print(f"CATALOGUE FETCH FAILED: {type(e).__name__}: {e}. "
                  "No purchase was made; retry the command.", file=sys.stderr)
            return 5
        print(f"{len(miners)} live miners for {args.intent}")
        for entry in miners:
            print(json.dumps(entry)[:300])
        return 0

    wanted = []
    if args.providers:
        wanted = [p.strip() for p in args.providers.split(",") if p.strip()]
    if args.miner:
        wanted.append(args.miner.strip())
    if not args.traps or not wanted:
        print("NO PURCHASE MADE: a live run needs --traps <json> and "
              "--providers <id[,id...]> (or --miner <id>). Nothing was bought.",
              file=sys.stderr)
        return 3

    # Trap set first: its sha256 is recorded in every output file, and
    # a bad trap file must fail before any network or spend.
    try:
        trap_doc, traps, traps_sha256 = load_traps(args.traps)
    except (OSError, ValueError, KeyError) as e:
        print(f"TRAP FILE ERROR: {args.traps}: {e}", file=sys.stderr)
        return 3
    by_id = {t["trap_id"]: t for t in trap_doc["traps"]}
    print(f"{len(traps)} traps from {args.traps} "
          f"(sha256 {traps_sha256[:16]}...)")

    # Output path: append-only. Refuse to overwrite an existing file
    # unless --append; on --append the trap set must match.
    out_path = Path(args.out) if args.out else None
    existing_doc = None
    existing_pairs = set()
    if out_path is not None and out_path.exists():
        if not args.append:
            print(f"REFUSED: output file already exists: {out_path}. "
                  "The runner is append-only and never overwrites a "
                  "results file. Re-run with --out <new file>, or pass "
                  "--append to add new rows to this file (already-scored "
                  "pairs are not re-bought).", file=sys.stderr)
            return 6
        try:
            existing_doc = json.loads(out_path.read_text())
        except (OSError, ValueError) as e:
            print(f"REFUSED: --append target is not a readable results "
                  f"file: {out_path}: {e}", file=sys.stderr)
            return 6
        if existing_doc.get("traps_sha256") != traps_sha256:
            print(f"REFUSED: --append target {out_path} was written for a "
                  "different trap set (sha256 mismatch). Different traps "
                  "go in a new --out file.", file=sys.stderr)
            return 7
        existing_pairs = {(r.get("trap_id"), r.get("provider_id"))
                          for r in existing_doc.get("scores") or []}
        print(f"--append: {len(existing_pairs)} scored pairs already in "
              f"{out_path}; they will not be re-bought.")
    if out_path is None and not args.dry_run:
        print("NO PURCHASE MADE: --out <results file> is required for a "
              "live run (the runner never overwrites; point it at a new "
              "file, or an existing one with --append). Nothing was bought.",
              file=sys.stderr)
        return 3

    # Key file: friendly error, zero spend, zero network. Checked
    # before any catalogue fetch or purchase — and before the payment
    # provider is constructed (unless one was injected, e.g. by tests).
    key_path = Path(args.key)
    key = None
    if payment_provider is None:
        try:
            key = read_key_file(key_path)
        except MissingKeyError as e:
            print(str(e), file=sys.stderr)
            return 4
        payment_provider = make_x402_provider(key, validity_seconds=55)

    client = DirectAskClient(transport=transport or curl_transport,
                             payment_provider=payment_provider,
                             max_call_usd=MAX_CALL_USD)

    # Resolve the requested providers against a FRESH catalogue fetch.
    # A re-run scores whoever the catalogue returns for these ids;
    # an id absent from the catalogue is refused, never bought stale.
    # The fetch is a free GET; the engine can truncate a chunked
    # response, so one retry is allowed before refusing cleanly.
    miners = None
    last_err = None
    for attempt in range(2):
        try:
            miners = client.miners(args.intent)
            break
        except Exception as e:  # noqa: BLE001 — any transport failure
            last_err = e
            print(f"catalogue fetch attempt {attempt + 1} failed "
                  f"({type(e).__name__}: {e}); retrying once...",
                  file=sys.stderr)
    if miners is None:
        print(f"CATALOGUE FETCH FAILED: {type(last_err).__name__}: "
              f"{last_err}. No purchase was made; retry the command.",
              file=sys.stderr)
        return 5
    by_mid = {}
    for entry in miners:
        if isinstance(entry, dict):
            mid = entry.get("id") or entry.get("miner_id") or entry.get("minerId")
            if mid is not None:
                by_mid[str(mid)] = entry
    print(f"{len(by_mid)} live miners in fresh catalogue: {sorted(by_mid)}")
    missing = [w for w in wanted if w not in by_mid]
    if missing:
        print(f"REFUSED: provider(s) {missing} not in the freshly fetched "
              f"catalogue for {args.intent}; refusing to buy from a stale "
              f"id. Live miners: {sorted(by_mid)}", file=sys.stderr)
        return 5
    provider_ids = wanted
    for mid in provider_ids:
        print(f"provider {mid}: {by_mid[mid].get('name')} "
              f"(catalogue cost_per_call is NOT a price — price comes "
              f"from the live 402 challenge)")

    run_id = _new_run_id()
    if args.dry_run:
        n_new = sum(1 for t in traps for mid in provider_ids
                    if (t.trap_id, mid) not in existing_pairs)
        print(f"DRY RUN OK: {len(traps)} traps x {len(provider_ids)} "
              f"providers = {n_new} new (trap, provider) pairs, "
              f"max cost ${n_new * CALL_PRICE_USD:.2f} at the "
              f"${CALL_PRICE_USD:.2f}/call docs figure (per-call ceiling "
              f"${MAX_CALL_USD:.2f}, cap ${args.spend_cap:.2f}), run-id "
              f"would be {run_id}, output would go to "
              f"{out_path or '(no --out given)'}. "
              f"Nothing bought, nothing written.")
        return 0

    bal_before, eth_before = balance_reader(BURNER)
    print(f"burner before: {bal_before} test USDC, {eth_before} Sepolia ETH")

    rows = list(existing_doc.get("scores") or []) if existing_doc else []
    new_rows = []
    spent = 0.0
    escrow_credit = 0.0
    if existing_doc:
        spent = float(existing_doc.get("total_cost_usd") or 0)
        escrow_credit = float(existing_doc.get("escrow_credit_usd") or 0)

    # Spend guard (F4): the live 402 challenge amount is checked
    # against the remaining cap BEFORE any payment is attempted, so
    # the cap is charged against the challenge amount, not the assumed
    # $0.01. The pre-loop check below is only the cheap planning
    # check; this guard is authoritative. Reads ``spent`` at call
    # time (closure over the local, which the loop updates).
    def spend_guard(amount_usd):
        return spent + amount_usd <= args.spend_cap
    client.spend_guard = spend_guard

    def save():
        doc = dict(existing_doc) if existing_doc else {}
        doc.update({
            "data_kind": "LIVE",
            "run": run_id,
            "run_ids": ([*(existing_doc.get("run_ids") or [])]
                        if existing_doc else []) + [run_id],
            "intent": args.intent,
            "traps_file": args.traps,
            "traps_sha256": traps_sha256,
            "freeze_time_utc": trap_doc.get("freeze_time_utc"),
            "provider_ids": provider_ids,
            "providers": {mid: by_mid[mid].get("name") for mid in provider_ids},
            "substitutions": [],
            "spend_cap_usd": args.spend_cap,
            "total_cost_usd": round(spent, 4),
            "escrow_credit_usd": round(escrow_credit, 4),
            "burner_balance_before_usdc": bal_before,
            "burner_eth_before": eth_before,
            "scores": rows,
        })
        # Atomic (F8): temp file + fsync + rename, so a crash mid-write
        # cannot corrupt the results file.
        atomic_write_text(out_path, json.dumps(doc, indent=2))

    def buy_once(trap, miner_id):
        # F12: pass the catalogue entry already fetched above instead
        # of re-fetching the catalogue for every buy.
        return client.buy_result(args.intent, miner_id,
                                 {"tx_hash": trap.tx_hash, "chain": "base-sepolia"},
                                 miner_entry=by_mid[miner_id])

    for trap in traps:
        for miner_id in provider_ids:
            label = f"{trap.trap_id} x {miner_id}"
            if (trap.trap_id, miner_id) in existing_pairs:
                print(f"{label}: already scored in {out_path} — skipping, no re-buy")
                continue
            if spent + CALL_PRICE_USD > args.spend_cap:
                print(f"CAP: stopping before {label} (spent {spent})")
                row = {**fail_row(trap, miner_id, "spend cap reached, not attempted"),
                       "skipped_cap": True}
                rows.append(row)
                new_rows.append(row)
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
                        # Full error string to fail_row: it parses the
                        # payment.status structurally and truncates the
                        # stored field itself (F7).
                        row = fail_row(trap, miner_id,
                                       f"{type(e2).__name__}: {str(e2)}")
                        rows.append(row)
                        new_rows.append(row)
                        escrow_credit += float(row.get("escrow_credit_usd") or 0)
                        save()
                        continue
                else:
                    print(f"{label}: FAILED: {type(e).__name__}: {str(e)[:200]} "
                          f"(a failed call may still have settled $0.01 "
                          f"into escrow credit — never assumed $0)")
                    row = fail_row(trap, miner_id,
                                   f"{type(e).__name__}: {str(e)}")
                    rows.append(row)
                    new_rows.append(row)
                    escrow_credit += float(row.get("escrow_credit_usd") or 0)
                    save()
                    continue
            if result.charged:
                # Charge the cap against what the call actually cost:
                # the served cost when reported, else the 402 challenge
                # amount that was signed (F4) — never an assumed $0.
                spent += float(result.cost_usd
                               if result.cost_usd is not None
                               else (result.challenge_amount_usd or 0))
            row = build_scored_row(trap, by_id[trap.trap_id], miner_id,
                                   args.intent, result)
            print(f"{label}: charged={result.charged} cost={result.cost_usd} "
                  f"passed={row['passed']} status={row['normalised_answer'].get('status')!r} "
                  f"norm={row['normalisation_notes']}")
            rows.append(row)
            new_rows.append(row)
            save()

    # Verify settlement receipts on-chain for the new rows only.
    # Post-loop failures must NOT propagate as a traceback: the rows
    # are already saved, so record the failure in the output doc and
    # exit non-zero cleanly (F8).
    verification_error = None
    try:
        verified, total = receipt_verifier(new_rows)
        if total:
            print(f"receipts verified on-chain: {verified}/{total} settled")
    except Exception as e:  # noqa: BLE001 — any verifier/RPC failure
        verification_error = f"{type(e).__name__}: {e}"
        print(f"RECEIPT VERIFICATION FAILED: {verification_error}. "
              f"Rows are already saved in {out_path}; totals below are "
              f"recorded where available.", file=sys.stderr)

    balance_error = None
    bal_after = eth_after = None
    try:
        bal_after, eth_after = balance_reader(BURNER)
    except Exception as e:  # noqa: BLE001 — any balance/RPC failure
        balance_error = f"{type(e).__name__}: {e}"
        print(f"BALANCE READ FAILED: {balance_error}. Rows are already "
              f"saved in {out_path}; after-balances are unavailable.",
              file=sys.stderr)

    doc = json.loads(out_path.read_text())
    doc["run"] = run_id
    # Persist the post-loop receipt verification flags: verify_receipts
    # mutates the in-memory rows in place, and the disk copy re-read
    # above predates those mutations — without this line the verified
    # flags (and settlement tx hashes) were silently discarded on
    # every run through this runner (found 9 Nov 2026: the 8 Nov
    # replay file and the expansion files all carried zero
    # receipt_verified_onchain flags despite "24/24 settled" logs).
    doc["scores"] = rows
    run_ids = list(doc.get("run_ids") or [])
    if run_id not in run_ids:
        run_ids.append(run_id)
    doc["run_ids"] = run_ids
    doc["total_cost_usd"] = round(spent, 4)
    doc["escrow_credit_usd"] = round(escrow_credit, 4)
    if bal_after is not None:
        doc["burner_balance_after_usdc"] = bal_after
        doc["burner_eth_after"] = eth_after
        doc["balance_drop_usdc"] = round(bal_before - bal_after, 4)
    if verification_error:
        doc["receipt_verification_error"] = verification_error
    if balance_error:
        doc["balance_read_error"] = balance_error
    atomic_write_text(out_path, json.dumps(doc, indent=2))
    if verification_error or balance_error:
        print(f"DONE WITH POST-LOOP ERRORS ({run_id}): {len(new_rows)} "
              f"new rows, spent ${spent:.2f}; see receipt_verification_error / "
              f"balance_read_error in {out_path}.", file=sys.stderr)
        return 8
    print(f"DONE ({run_id}): {len(new_rows)} new rows, spent ${spent:.2f}, "
          f"balance {bal_before} -> {bal_after} USDC (drop {bal_before - bal_after:.2f}), "
          f"ETH {eth_before} -> {eth_after}")
    for mid in provider_ids:
        rs = [r for r in new_rows if r.get("provider_id") == mid and not r.get("skipped_cap")]
        p = sum(1 for r in rs if r.get("passed"))
        print(f"  {mid}: {p}/{len(rs)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
