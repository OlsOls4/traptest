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
truncated) plus `receipt_settlement_tx` where recorded. Where a served row records no
`receipt_settlement_tx` (all 12 Truvian rows), the page falls back to the
`tx_hash` inside the row's base64 Telegraph receipt and links that to
Sepolia Etherscan, so all 24 served rows show a settlement link. Ranking
(implemented in the page, mirroring `traptest/leaderboard.py`): pass rate,
then traps run, then lower total testnet cost, then provider id — computed
over served traps only. Providers that served zero traps are excluded from
the ranked table entirely and shown in a separate "Unservable — no pass
rate" tier with no pass-rate column; the ranked table lists only served
providers (Truvian 8453, TxLens 9002 in the shipped file). Fixed 9 Nov
2026 — the page previously recomputed a pass rate from raw rows and
displayed the unservable providers as ranked 3rd/4th/5th at 0%, which the
verdict box, this README and `traptest/leaderboard.py` all contradict.
Unserved rows show their returned error string and receipts
"n/a (not served)", never "MISSING". Each per-trap detail shows the trap's
category, its Base Sepolia tx hash (linked to sepolia.basescan.org), and
any escrow credit settled for the call (`escrow_credit_usd` — $0.01 per
failed Sigil/OnChain Intel call, $0.12 per provider). A 12×2 comparison
matrix (traps × served providers) shows PASS/FAIL per trap; Truvian and
TxLens diverge on t07/t08.

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
scored purchase of the run; SHA-256
`0f84494bc8a6b1773aa74f2f9e3c15b6e7eb42b397c8849bbea3068bd4a1d534`, also
rendered on the page from `results.json`). The page is a frozen snapshot:
run 6 Nov 2026, re-scored 8 Nov, not live-updating (stamped above the
ranked table). Demo video v2 is the public YouTube link
https://youtu.be/993JOD3JRXs. Anjoman eval pool evidence: 702 eligible
rows, 5 submitters — https://anjoman.ai/dashboard/eval. One-command
dry-run replay (spends nothing, writes nothing; build the 1-trap replay
file and fund a burner first, see `docs/how-to-run.md` §4):

```bash
python3 -m traptest.run --traps traps-replay-2026-11-08.json --providers 9002,8453 --key .burner-replay.key --out results-live/replay-2026-11-08.json --dry-run
```

An empty `.nojekyll` file at the repo root keeps GitHub Pages from
mangling `.md` links if the repo is ever published that way.

## Expansion set t13–t24 (9 Nov 2026) — separate section, separate file

`results-expansion.json` (36 served rows) renders as its own section on
the page (`renderExpansion()` in `index.html`), below the frozen-set
tables. It is NOT a re-score of the frozen set: the expansion traps
(`traps-frozen-2026-11-09.json`, SHA-256
`940a00400477e0aefb38afe1da20fb98cc03b187e7218da252d322fd4699b5ba`) use
scoring v2 — token traps score the native tx value (0 wei for t13/t14),
unknown traps carry the strict-unknown rule. Results: ChainWire 1707307
(Cross-Checked) 11/12, field accuracy 46/47 (only t17 fails — reverted
tx value returned 0, expected 607000000000000 wei); Truvian 8453 2/12
(t17, t18; field 39/49); TxLens 9002 2/12 (t23, t24; field 2/47).
Truvian's t23/t24 fail only under the v2 rule, on its `from` source
label ("Truvian onchain lookup over public JSON-RPC") — a provenance
string, not a hallucinated address; disclosed on the page. Verity 9001
(HTTP 500 upstream 404) and INTERLOCK 9007 (HTTP 503
`no_compatible_miner`) served 0 — unservable tier. ChainWire 7317307 and
7307 each served and passed the t13 probe only (receipts verified);
their full sets were not run (task $0.50 cap allowed one full new-miner
set, run on 1707307) and they are not ranked on 1 trap. Combined
24-trap numbers (frozen + expansion, NOT one uniform measure): TxLens
4/24 (field 4/94), Truvian 6/24 (field 76/96 — the 96 denominator
includes the 2 extra v2 fields on Truvian's unknown rows; v1-basis
76/94). Expansion task spend: $0.42 wallet drop (cap $0.50): $0.24
expansion run + $0.12 ChainWire 1707307 full set + $0.03 probes billed
+ $0.03 Verity escrow credit; wallet 29.26 → 28.84 test USDC. The 7
cap-skipped rows in `results-live/expansion-run-2026-11-09.json`
(1707307 t18–t24, stopped by the file-cumulative $0.30 cap) are
excluded from this file; the 7 bought rows live in
`results-live/expansion-run-1707307-rest-2026-11-09.json`. Render check:
`node render-check.cjs` in this folder (20 assertions, no dependencies)
— it verifies the frozen tables still render exactly 2 ranked rows,
the unservable tier, and 24/24 settlement links, plus the expansion
tables (3 ranked rows, 12-trap matrix, 36/36 settlement links).
