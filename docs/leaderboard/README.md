# TrapTest leaderboard — static page

Zero-cost, no hosting dependency, no paid service, no account: plain
HTML/CSS/JS in `index.html`, rendered from `results.json` in this folder.

## Open it (prep / mock mode)

```bash
cd docs/leaderboard
python3 -m http.server
# open http://localhost:8000/
```

Opening `index.html` directly (`file://`) blocks the `results.json` fetch in
most browsers — use the local server above, or the file picker on the page.

## Data contract

`results.json` must carry `"data_kind": "MOCK"` for this page to render it —
the page refuses to render any file not labelled MOCK, so a live results
file can never be silently displayed as mock (or vice versa). Each score
row: `trap_id`, `provider_id`, `passed`, `fields` (each with `field`,
`expected`, `actual`, `passed`), `cost_usd`, `signal_hash`,
`receipt_present`. Ranking (implemented in the page, mirroring
`traptest/leaderboard.py`): pass rate, then traps run, then lower total
testnet cost, then provider id. Zero-trap providers are listed as
unranked, never as passing.

## MOCK warning

The shipped `results.json` is a prep fixture with invented provider ids
(`mock-provider-a/b/c`) and invented trap hashes. It is NOT event evidence
and must never be submitted, quoted, or screenshotted as a real result.
The live results file — written only from event-period purchases with
real `cost_usd`, `signal_hash` and `X-TELEGRAPH-RECEIPT` values — replaces
it in the live build, and every mock surface must be removed or relabelled
before submission (see `docs/submission-pack.md`).
