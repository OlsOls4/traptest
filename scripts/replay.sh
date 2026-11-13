#!/usr/bin/env bash
# TrapTest one-command stranger entry point: tests -> live miner
# discovery -> dry-run (spends $0, writes nothing) -> serve the
# leaderboard locally.
#
# Usage:  ./scripts/replay.sh
#   or:   TRAPTEST_BURNER_ADDRESS=0x... ./scripts/replay.sh
#         (prints mint instructions for that burner address)
#
# The dry-run uses your real burner key when .burner3.key exists
# (TRAPTEST_KEY overrides the path). On a fresh clone with no key
# yet, it uses a temporary throwaway key (generated in /tmp, deleted
# afterwards, never funded) purely so the dry-run can validate the
# full path — and then prints the copy-paste mint instructions so
# you can fund a real burner. Nothing here buys anything, writes a
# results file, or touches a private key.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1/4 tests =="
python3 -m unittest discover -s tests

echo "== 2/4 live miners (free discovery, no purchase) =="
python3 -m traptest.run --list-miners

echo "== 3/4 dry-run (24 traps x 2 providers, \$0 spent) =="
KEY="${TRAPTEST_KEY:-.burner3.key}"
TMP_KEY=""
if [ -f "$KEY" ]; then
  DRY_KEY="$KEY"
  echo "using burner key file: $KEY"
else
  # Throwaway key for validation only: fresh, unfunded, deleted below.
  TMP_KEY="$(mktemp /tmp/traptest-dry-run-key-XXXXXX)"
  python3 - "$TMP_KEY" <<'PY'
import sys
from eth_account import Account
path = sys.argv[1]
acct = Account.create()
with open(path, "w") as f:
    f.write("0x" + acct.key.hex())
print("no burner key file found: dry-run uses a temporary throwaway key")
print(f"temporary dry-run payer (unfunded, deleted after this run): {acct.address}")
PY
  DRY_KEY="$TMP_KEY"
fi
OUT="$(mktemp -u /tmp/traptest-dry-run-XXXXXX.json)"
python3 -m traptest.run --traps traps-frozen-2026-11-09.json \
  --providers 9002,8453 --key "$DRY_KEY" \
  --out "$OUT" --dry-run
if [ -n "$TMP_KEY" ]; then
  rm -f "$TMP_KEY"
  echo
  echo "== mint instructions (no funded burner yet) =="
  python3 scripts/fund_burner.py ${TRAPTEST_BURNER_ADDRESS:+--address "$TRAPTEST_BURNER_ADDRESS"}
  echo "Save your burner key (hex, 0x-prefixed, mode 600) to .burner3.key,"
  echo "fund it with the mint above, then re-run ./scripts/replay.sh."
fi

echo
echo "== 4/4 leaderboard (local) =="
echo "Serving docs/leaderboard at http://localhost:8123/ (Ctrl-C to stop)"
python3 -m http.server 8123 --directory docs/leaderboard
