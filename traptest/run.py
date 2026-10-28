"""TrapTest live runner — GATED. Refuses any live purchase unless BOTH:

(a) the current UTC date is on/after 2026-11-01 (the Season II window), and
(b) an explicit activation marker file exists.

Default marker: <repo>/LIVE-ACTIVATED (override with --marker or the
TRAPTEST_ACTIVATION_MARKER env var). The marker is created by a human on
day 1 ONLY after the free-testnet gate passes (faucet claim landed in a
burner wallet at Telegraph's USDC contract) — creating it is NOT this
script's job and this script never creates wallets, claims faucets, or
holds keys.

Gate failure: prints GATE REFUSED to stderr and exits 2, having made NO
network purchase (indeed, no network call at all — the gate is checked
before any client is constructed).

Even with both gates passed, this runner still makes NO purchase unless
it is also given a trap set (--traps <json>) AND a payment provider, which
prep deliberately does not ship: the day-1 burner-wallet module must
supply it. With gates passed but those missing, it exits 3 with a plain
explanation and no spend. --list-miners (free discovery only, no purchase)
is the only network action available with gates passed and no payment
provider.

Trap JSON format: [{"trap_id","intent","tx_hash","expected_status",
"expected_from","expected_to","expected_value","expected_block"}].
Ground truth must be checked against public chain data in the event
window before running — never invented, never tuned to flatter a provider.
"""
import argparse
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

WINDOW_OPEN = date(2026, 11, 1)
DEFAULT_MARKER = Path(__file__).resolve().parent.parent / "LIVE-ACTIVATED"


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


def main(argv=None, today=None):
    parser = argparse.ArgumentParser(description="TrapTest live runner (gated)")
    parser.add_argument("--intent", default="ONCHAIN_TX_LOOKUP")
    parser.add_argument("--miner", help="miner id (verified against fresh catalogue)")
    parser.add_argument("--traps", help="path to trap-set JSON (event-window ground truth)")
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

    # Network only happens from here on, and only free discovery unless a
    # payment provider is supplied by the (not yet written) day-1 module.
    try:
        from .providers import DirectAskClient  # package execution
    except ImportError:  # direct script execution: python traptest/run.py
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from traptest.providers import DirectAskClient

    client = DirectAskClient()  # no payment_provider in prep: 402s raise, no spend
    if args.list_miners:
        miners = client.miners(args.intent)
        print(f"{len(miners)} live miners for {args.intent}")
        for entry in miners:
            print(json.dumps(entry)[:300])
        return 0

    if not args.traps or not args.miner:
        print("NO PURCHASE MADE: a live run needs --traps <json> and --miner <id>, "
              "plus a payment provider from the day-1 burner-wallet module "
              "(not shipped in prep). Nothing was bought.", file=sys.stderr)
        return 3
    print("NO PURCHASE MADE: payment provider not configured in prep; "
          "wire the day-1 burner-wallet module before running traps.",
          file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
