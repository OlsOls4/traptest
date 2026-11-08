# TrapTest leaderboard — static page

Zero-cost, no hosting dependency, no paid service, no account: plain
HTML/CSS/JS in `index.html`, rendered from `results.json` in this folder.

## Open it (live mode)

```bash
cd docs/leaderboard
python3 -m http.server
# open http://localhost:8000/
```

Opening `index.html` directly (`file://`) blocks the `results.json` fetch in
most browsers — use the local server above, or the file picker on the page.

## Data contract

`results.json` must carry `"data_kind": "LIVE"` or `"data_kind":
"CORRECTED_REANALYSIS"` for this page to render it — the page refuses to
render any file not labelled one of those, so a mock fixture can never be
silently displayed as a live result (or vice versa). The shipped file is the
corrected re-analysis (`results-live/results-corrected-2026-11-08.json`):
top-level `data_kind: CORRECTED_REANALYSIS`, corrected scores under
`corrected.scores` (pass/fail in `corrected_passed`, raw answers unchanged),
the strict original preserved verbatim under `strict_original`, and the
t03/t04 value-excluded view under `value_excluded_view`. Each score row:
`trap_id`, `provider_id`, `passed`, `fields` (each with `field`, `expected`,
`actual`, `passed`), `cost_usd`, `signal_hash`, `receipt_present`, and for
served rows a base64 Telegraph receipt (decoded `receipt_hash` shown
truncated) plus `receipt_settlement_tx` where recorded. Ranking (implemented
in the page, mirroring `traptest/leaderboard.py`): pass rate, then traps run,
then lower total testnet cost, then provider id. Zero-trap providers are
listed as unservable, never as passing, and no pass rate is computed for
them. Unserved rows show their returned error string and receipts
"n/a (not served)", never "MISSING".

## LIVE data (6 Nov 2026 run, corrected re-score 8 Nov 2026)

The shipped `results.json` is the corrected re-score of the 6 Nov 2026 full
scored run: 12 frozen traps × 5 providers (TxLens 9002, LiveCert 4433,
Truvian 8453, Sigil 9010, OnChain Intel 900), 60 rows. Corrected: Truvian
4/12 (t07, t08, t11, t12; field accuracy 37/47), TxLens 2/12 (field accuracy
2/47); strict original was Truvian 3/12 (field accuracy 36/47) — only t08
changed, under the fixed normaliser. LiveCert/Sigil/OnChain Intel served
0/12 (LiveCert 503 on all 12; Sigil HTTP 500 upstream 404; OnChain Intel
HTTP 500 upstream 400) — unservable, not a 0% pass rate. Billed $0.26 total
including $0.02 smoke tests ($0.24 in the run file + $0.02 smoke); $0.24
settled into Telegraph escrow credit, NOT billed; wallet 30.00 → 29.50 test
USDC (drop $0.50). 24 served receipts verified on-chain. It REPLACED the
prep mock fixture (mock-provider-a/b/c, invented trap hashes) — that fixture
is gone from this folder and must never be quoted as a result. Source of
truth: `results-live/full-run-2026-11-06.json` (same rows, strict original)
and `results-live/results-corrected-2026-11-08.json` (corrected re-score);
traps in `traps-frozen-2026-11-06.json` (frozen 13:59:42Z, before the first
scored purchase of the run).
