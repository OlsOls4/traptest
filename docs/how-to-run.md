# TrapTest — how to run (reviewer guide)

Audience: a Telegraph Season II judge/reviewer reproducing TrapTest from
scratch. Read the MOCK warning first: **nothing in the prep scaffold is a
real result.** Mock fixtures demonstrate the UI and the scoring rules only.

## 0. What this is, in one paragraph

TrapTest (Evaluator-led, Telegraph Hackathon Season II, 1 Nov–1 Dec 2026)
buys fixed trap transaction queries — queries whose ground truth is known
in advance — from competing `ONCHAIN_TX_LOOKUP` providers on testnet,
scores each answer pass/fail against that truth, and publishes a
leaderboard that re-ranks providers. A provider that returns a stale or
wrong answer is shown failing, not hidden. That failure-on-screen is the
point of the entry: it is the thing that proves whether the ranking
itself can be trusted.

## 1. Prerequisites (zero cost)

- Python 3 (stdlib only for the scaffold; no pip packages, no API keys,
  no account, no hosting).
- A browser (for the static leaderboard page).
- For the LIVE loop only (from 1 Nov, after the gates in §5 pass): a
  burner wallet funded with free Base Sepolia testnet USDC/gas, and
  network access to `https://devnode.telegraphprotocol.com/engine`.
  No card, purchase, bridge, or mainnet spend is ever required or used.

## 2. Prep checks that work today (no Telegraph purchase)

```bash
# From ~/workspace/telegraph-traptest/
python3 -m unittest discover -s tests -v
# Expected: the mock-fixture tests pass (scoring strictness + ranking).
# These tests are NOT event evidence.

# Leaderboard UI (MOCK data — see the red banner on the page):
cd docs/leaderboard
python3 -m http.server
# Open http://localhost:8000/
```

What to check on the mock page: the ranking order (pass rate, then traps
run, then lower cost), the per-trap field table, the `FAIL` rows
(mock-provider-b fails one trap on a wrong `status` and one on a missing
`to` field), and the unranked provider listed separately with zero traps.

## 3. Judge-in-60-seconds path (live build, from 1 Nov)

1. **One input.** Enter a single trap transaction hash — a query with
   known ground truth from the fixed trap set (see §4). No login, no
   setup, no wallet connection on the reviewer's side.
2. **Competing answers bought.** TrapTest buys that trap from at least
   two competing `ONCHAIN_TX_LOOKUP` providers via Direct Ask
   (`POST /engine/v1/ask/{minerId}` — one miner at a time; the
   auto-routed ask cannot compare competitors). Miner ids are re-fetched
   from the live catalogue at run time, never hardcoded.
3. **Pass/fail with receipts.** Each answer is scored by
   `traptest/scoring.py`: status must match exactly (a status mismatch
   fails the trap outright), every scored field must match, and a
   missing provider field is a failure, never a pass. Each served call
   records `cost_usd`, `signal_hash`, and the Telegraph receipt
   (`X-TELEGRAPH-RECEIPT`). Price is read from the live 402 challenge,
   never from the catalogue's `cost_per_call: "0.00"` field.
4. **Leaderboard re-ranks.** `traptest/leaderboard.py` re-ranks by pass
   rate, then traps run, then lower total testnet cost. The page at
   `docs/leaderboard/` renders the live `results.json` in the same
   layout as the mock page — compare the two layouts, never the numbers.
5. **Failure case, on screen.** Pick a trap where a provider is stale or
   wrong (the live results file marks at least one such row) and confirm
   it renders `FAIL` with the mismatching field highlighted, and that
   the provider's pass rate drops accordingly. If no provider ever
   fails, say so honestly — a leaderboard with no failures is a weaker
   result, not a reason to invent one.

> Live-run command: **[TO FILL from 1 Nov, once the live purchase loop
> lands]** — the prep scaffold deliberately contains no purchase code
> path (`traptest/providers.py: ProviderClient.buy` raises
> `NotImplementedError` until the event window). Do not run, quote, or
> submit any live command until it exists in the repo and has been run
> against testnet in the event window. The reviewer steps above describe
> the loop the command must implement; they are not a claim that it
> already runs.

## 4. Reproduce from instructions (reviewer checklist)

- [ ] Trap set is fixed **before** scoring begins: confirm the trap file
  (ids, intents, tx hashes, expected status/from/to/value/block) is
  committed and unchanged after the first scored purchase. A set tuned
  after seeing answers — to flatter any provider — invalidates the run.
- [ ] Ground truth is checked against public chain data for each trap
  (status and decoded fields), not invented and not copied from a
  provider's answer.
- [ ] A **new input** works: supply a trap tx hash that is in the fixed
  set but was not in the demo video, run the loop, and confirm the new
  row appears scored with a receipt.
- [ ] **Inspect a receipt:** pick any scored row, confirm `cost_usd`,
  `signal_hash`, and a Telegraph receipt are recorded for that call,
  and that the cost matches the live 402 challenge for that miner.
- [ ] **Test a failure case:** confirm at least one failing row renders
  `FAIL` with the mismatching field named (status mismatch, or a
  missing field) — or, if none exists, record that honestly.
- [ ] **Reproduce the ranking:** re-run the aggregation from the raw
  scored rows and confirm the displayed order matches pass rate →
  traps run → lower cost.
- [ ] **Cost cap:** total testnet spend stays inside the confirmed free
  testnet allocation; the trap set is of the order of tens of traps ×
  2 providers (see `../README.md`). Any spend beyond that needs a
  fresh explicit approval — never a silent purchase or bridge.

## 5. Day-1 gates — live work must not start until all pass

1. **Prize-payment terms published** (rules say before the competition
   opens): confirm UK eligibility, payout currency/method, and timing.
   Registration alone confirms none of these.
2. **Free testnet USDC/gas obtained:** faucet claim into a burner wallet
   (funded only with what inference needs), balance confirmed at
   Telegraph's Base Sepolia USDC contract
   (`0x036CbD53842c5426634e7929541eC2318f3dCF7e`). A failed claim is a
   STOP — never buy or bridge with real money without Olly's explicit
   approval of that specific spend.
3. **Competing-provider supply re-confirmed live:** at least two
   usable `ONCHAIN_TX_LOOKUP` miners answer the trap intent at run
   time (27 Oct check found 23 miners, ≥10 usable after filtering
   list-only endpoints — re-fetch, do not reuse those ids).
4. **Evaluator-specific submission wording** confirmed in the live
   browser with the Evaluator track selected, before submitting.

## 6. Honest limits (say these on every surface)

- Testnet use is **not** adoption, and manufactured adoption (e.g. a
  self-purchase counted as a buyer) is a disqualifier. No adoption,
  user, accuracy, or time-saved figure exists for TrapTest yet — do not
  invent one.
- The entry is single-Intent (`ONCHAIN_TX_LOOKUP`); it does not claim
  coverage of other Intents.
- If the live leaderboard UI slips, the fallback is a scored table +
  receipts for the same fixed trap set — same evidence, plainer layout.
- Scores: judging is /100 (Technical 35, min 24; Commercial 30;
  Adoption 15; Integration 10; Proof 10; need 70+). TrapTest's honest
  ceiling on Adoption is low (see above); its case rests on Technical,
  Integration, and Proof.
