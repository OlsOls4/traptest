"""One-trap live test purchase (6 Nov 2026, event window).

Buys ONE trap answer from ONE ONCHAIN_TX_LOOKUP_GENERAL provider via
Direct Ask, using the x402 provider on burner 3, scores it against
ground truth fetched from public Base Sepolia chain data, and writes
the scored row to results-live/test-purchase-1.json (data_kind LIVE).

Cost: one $0.01 testnet call (self-minted test USDC, zero real money).
Run: python3 scripts/test_purchase_1.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from traptest.providers import (  # noqa: E402
    DirectAskClient, TransportHTTPError, USER_AGENT, _HttpResponse)
from traptest.scoring import score_answer  # noqa: E402
from traptest.traps import Trap  # noqa: E402
from traptest.x402 import make_x402_provider  # noqa: E402

INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
TX_HASH = "0xd47a090fee50ae43d3af7dcb03eced0be6c98a48b3aa92dc21a8c4d9d784ae96"
# Ground truth verified against Base Sepolia public RPC, 6 Nov 2026:
# tx 0xd47a09... block 53047427, receipt status 0x1 (confirmed),
# from 0xdeaddeaddeaddeaddeaddeaddeaddeaddead0001,
# to 0x4200000000000000000000000000000000000015, value 0.
TRAP = Trap(
    trap_id="t01-confirmed-transfer",
    intent=INTENT,
    tx_hash=TX_HASH,
    expected_status="confirmed",
    expected_from="0xdeaddeaddeaddeaddeaddeaddeaddeaddead0001",
    expected_to="0x4200000000000000000000000000000000000015",
    expected_value="0",
    expected_block=53047427,
)
PREFER_MINERS = ["9002", "4433", "9010", "900", "9001", "8453",
                 "20260828", "9007", "7307"]


def curl_transport(method, url, body, headers):
    """curl-backed transport (urllib POSTs to devnode fail intermittently
    from this VM; curl works reliably). Raises TransportHTTPError on
    HTTP >= 400, mirroring _urllib_transport."""
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


def main():
    key_path = Path(__file__).resolve().parent.parent / ".burner3.key"
    private_key = key_path.read_text().strip()
    # validity 55s: inside the challenge's maxTimeoutSeconds (60).
    provider = make_x402_provider(private_key, validity_seconds=55)
    client = DirectAskClient(transport=curl_transport,
                             payment_provider=provider)
    miners = client.miners(INTENT)
    print(f"{len(miners)} live miners for {INTENT}")
    by_id = {}
    for entry in miners:
        if isinstance(entry, dict):
            mid = entry.get("id") or entry.get("miner_id") or entry.get("minerId")
            if mid is not None:
                by_id[str(mid)] = entry
    chosen = next((m for m in PREFER_MINERS if m in by_id), None)
    if chosen is None:
        chosen = next(iter(by_id), None) if by_id else None
    if chosen is None:
        print("NO MINERS: catalogue empty, no purchase made")
        return 2
    print(f"chosen miner: {chosen} -> {json.dumps(by_id[chosen])[:200]}")
    result = client.buy_result(
        INTENT, chosen, {"tx_hash": TX_HASH, "chain": "base-sepolia"})
    print(f"served: charged={result.charged} cost_usd={result.cost_usd} "
          f"signal={result.signal_hash} receipt_present={bool(result.receipt)}")
    print(f"answer: {json.dumps(result.answer)[:1000]}")
    score = score_answer(TRAP, chosen, result.answer,
                         cost_usd=result.cost_usd,
                         signal_hash=result.signal_hash,
                         receipt_present=bool(result.receipt))
    print(f"SCORE: passed={score.passed}")
    for f in score.fields:
        print(f"  {f.field}: expected={f.expected} actual={f.actual} "
              f"passed={f.passed}")
    out = {
        "data_kind": "LIVE",
        "trap_id": TRAP.trap_id,
        "intent": INTENT,
        "tx_hash": TX_HASH,
        "miner_id": chosen,
        "cost_usd": result.cost_usd,
        "signal_hash": result.signal_hash,
        "receipt_present": bool(result.receipt),
        "receipt": result.receipt,
        "answer": result.answer,
        "passed": score.passed,
        "fields": [{"field": f.field, "expected": f.expected,
                    "actual": f.actual, "passed": f.passed}
                   for f in score.fields],
        "provenance": {
            "ground_truth_source": "Base Sepolia public RPC, 6 Nov 2026",
            "block": 53047427,
            "payer": "burner 3 (testnet only), 30 self-minted test USDC",
            "settlement": "Ethereum Sepolia, x402 exact, $0.01/call",
        },
    }
    out_path = (Path(__file__).resolve().parent.parent
                / "results-live" / "test-purchase-1.json")
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
