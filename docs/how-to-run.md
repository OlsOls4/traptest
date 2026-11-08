# TrapTest — how to run (reviewer guide)

Audience: a Telegraph Season II judge/reviewer reproducing TrapTest from
scratch. **Live build, 6 Nov 2026, corrected re-score 8 Nov 2026: the full
scored run is done — 12 frozen traps × 5 providers, 60 rows,
`results-live/full-run-2026-11-06.json` (`data_kind: LIVE`, strict
original) and `results-live/results-corrected-2026-11-08.json` (corrected:
Truvian 4/12, TxLens 2/12), rendered at `docs/leaderboard/`.** Mock
fixtures exist only in `tests/` (framework testing, labelled MOCK, never
event evidence).

## 0. What this is, in one paragraph

TrapTest (Evaluator-led, Telegraph Hackathon Season II, 1 Nov–1 Dec 2026)
buys fixed trap transaction queries — queries whose ground truth is known
in advance — from competing `ONCHAIN_TX_LOOKUP_GENERAL` providers on testnet,
scores each answer pass/fail against that truth, and publishes a
leaderboard that re-ranks providers. A provider that returns a stale or
wrong answer is shown failing, not hidden. That failure-on-screen is the
point of the entry: it is the thing that proves whether the ranking
itself can be trusted.

## 1. Prerequisites (zero cost)

- Python 3 (stdlib only for the scaffold; no pip packages, no API keys,
  no account, no hosting).
- A browser (for the static leaderboard page).
- For the LIVE loop only: a burner wallet holding Telegraph's accepted
  test USDC (`0xcc194e1a843B658526D0D5C431f670028582Ae17` on Ethereum
  Sepolia, self-minted via the token's open mint — no Telegraph faucet
  exists) plus a little Sepolia ETH for the one-time mint, and network
  access to `https://devnode.telegraphprotocol.com/engine`. No card,
  purchase, bridge, or mainnet spend is ever required or used. The
  6 Nov run used burner 3 (`0x170DfA67D1e37915d8130eaB9bD3b0a4E115f0C0`);
  its key is local-only (`.burner3.key`, mode 600, never committed) —
  a reviewer re-running the loop funds their own burner the same way.

## 2. Prep checks that work today (no Telegraph purchase)

```bash
# From ~/workspace/telegraph-traptest/
python3 -m unittest discover -s tests -v
# Expected: 91 tests pass (scoring strictness + ranking + gates +
# parametrised-runner guards: no-overwrite, missing-key, dry-run,
# append-without-duplicates).
# These tests use MOCK fixtures and are NOT event evidence.

# Leaderboard (LIVE data — the 6 Nov 2026 run, 60 rows):
cd docs/leaderboard
python3 -m http.server
# Open http://localhost:8000/
```

What to check on the live page: the verdict strip (Truvian 4/12 vs TxLens 2/12
— a two-trap margin on n=12, evidence not a proven gap), the ranking order
(pass rate, then traps run, then lower cost), the corrected table beside the
strict original (Truvian 3/12), the per-trap field table, the `FAIL` rows
(TxLens fails 10 traps on a wrong `status` — it answers `not_found` for
every mined tx; Truvian fails 8, six of them only on a missing `status`
for confirmed txs), and the unservable providers listed at 0/12 served with
their returned error strings (LiveCert 503 on all 12; Sigil HTTP 500 upstream
404; OnChain Intel HTTP 500 upstream 400).

## 3. Judge-in-60-seconds path (live build, from 1 Nov)

1. **One input.** Enter a single trap transaction hash — a query with
   known ground truth from the fixed trap set (see §4). There is no live
   in-page loop: replaying the loop needs the reviewer's own burner wallet,
   funded with test USDC as in §1 (self-minted via the token's open mint
   plus a little Sepolia ETH for gas). The pre-run evidence — the
   leaderboard, the corrected results file, and every receipt — is the
   default: it costs nothing to inspect and is what a reviewer should check
   first.
2. **Competing answers bought.** TrapTest buys that trap from at least
   two competing `ONCHAIN_TX_LOOKUP_GENERAL` providers via Direct Ask
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
   `docs/leaderboard/` renders the corrected re-score
   (`docs/leaderboard/results.json`, copy of
   `results-live/results-corrected-2026-11-08.json` — corrected Truvian 4/12,
   TxLens 2/12, strict original 3/12/2/12 preserved alongside). The prep mock
   page is gone — the fixture was replaced by the live file, not
   deleted while still showing mock data.
5. **Failure case, on screen.** Pick a trap where a provider is stale or
   wrong (the live results file marks at least one such row) and confirm
   it renders `FAIL` with the mismatching field highlighted, and that
   the provider's pass rate drops accordingly. If no provider ever
   fails, say so honestly — a leaderboard with no failures is a weaker
   result, not a reason to invent one.

> Live-run commands — the replay path for a judge is the
> parametrised runner (`traptest/run.py`). It takes a trap file,
> provider ids and an output path, resolves providers against a fresh
> catalogue fetch, and refuses to overwrite any existing results file:
>
> ```bash
> # 1-trap replay with a NEW trap hash (build the trap file and fund
> # a burner first — see §4):
> python3 -m traptest.run --traps traps-replay-2026-11-08.json \
>     --providers 9002,8453 \
>     --out results-live/replay-2026-11-08.json
>
> # Validate everything first without spending or writing anything:
> python3 -m traptest.run --traps traps-replay-2026-11-08.json \
>     --providers 9002,8453 --out results-live/replay-2026-11-08.json \
>     --dry-run
>
> # Append more providers to the same file later (already-scored
> # pairs are not re-bought or duplicated):
> python3 -m traptest.run --traps traps-replay-2026-11-08.json \
>     --providers 9010 --out results-live/replay-2026-11-08.json --append
> ```
>
> Historical runs (6 Nov 2026; their results file is frozen and they
> now refuse to write to it — they need `--out <new file>`):
>
> ```bash
> python3 scripts/full_run.py --out results-live/full-replay.json
> python3 scripts/mini_run.py --out results-live/mini-replay.json
> ```
>
> All three runners read a trap set, buy via Direct Ask with the x402
> provider on a burner key, score with `traptest/scoring.py`, and
> write `data_kind: LIVE` rows. The runner records the trap file's
> sha256 in every output file, so a re-run can be checked against the
> exact trap set it scored. One attempt per trap+miner (single retry
> only for a transport failure before any payment). Session spend cap
> $0.50 (billed); see §4 for the accounting, including the
> escrow-credit finding. A re-run scores whoever the live catalogue
> returns for the requested ids on that day — miner ids are not
> stable, so a replay's provider set may differ from 6 Nov.

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
  row appears scored with a receipt. Concrete replay with a new trap
  hash (all commands from the repo root; nothing here overwrites the
  frozen 6 Nov results):
  1. Pick a Base Sepolia tx and verify its ground truth against the
     public RPC (`https://base-sepolia-rpc.publicnode.com`:
     `eth_getTransactionByHash` + `eth_getTransactionReceipt` for
     status/from/to/value/block). Never copy ground truth from a
     provider's answer.
  2. Write it as a 1-trap file, e.g. `traps-replay-2026-11-08.json`:
     `{"intent": "ONCHAIN_TX_LOOKUP_GENERAL", "traps": [{"trap_id":
     "r01-new-trap", "intent": "ONCHAIN_TX_LOOKUP_GENERAL", "tx_hash":
     "0x…", "expected_status": "confirmed", "expected_from": "0x…",
     "expected_to": "0x…", "expected_value": "0",
     "expected_block": 12345678}]}`. Freeze it before scoring.
  3. Fund a burner: create a disposable testnet-only key, save it
     (hex, 0x-prefixed, mode 600) to `.burner-replay.key`; get Sepolia
     ETH for gas from the PoW faucet
     (`https://sepolia-faucet.pk910.de`); mint the accepted test USDC
     (`0xcc194e1a843B658526D0D5C431f670028582Ae17` on Ethereum Sepolia,
     open `mint()` — there is no Telegraph faucet; NOT Circle faucet
     USDC `0x1c7d…`). If the key file is missing the runner exits
     non-zero printing these exact steps and spends nothing.
  4. Create the activation marker (only in the event window, 1 Nov–
     1 Dec 2026): `touch LIVE-ACTIVATED`.
  5. Dry-run first (validates traps, key, providers, output path;
     spends and writes nothing):
     `python3 -m traptest.run --traps traps-replay-2026-11-08.json
     --providers 9002,8453 --key .burner-replay.key
     --out results-live/replay-2026-11-08.json --dry-run`
  6. Run it (max $0.02 for 1 trap × 2 providers; default cap $0.30):
     same command without `--dry-run`. The output file records the
     trap file's sha256 (`traps_sha256`) — confirm it matches
     `sha256sum traps-replay-2026-11-08.json`. A second run with
     `--append` to the same file adds no duplicate rows and buys
     nothing already scored; pointing `--out` at an existing file
     without `--append` is refused.
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
  testnet allocation; the trap set is 12 traps × 5 providers (60 rows).
  Session accounting, verified on-chain 6 Nov 2026: billed $0.26 total
  including $0.02 smoke tests ($0.24 in the run file + $0.02 smoke);
  $0.24 settled into Telegraph escrow credit, NOT billed (Sigil $0.12 +
  OnChain Intel $0.12 — a failed call can still settle $0.01 on-chain;
  Telegraph's message says the amount is credited to escrow, and the burner
  balance drop confirms it); burner wallet 30.00 → 29.50 test USDC (drop
  $0.50). Billed spend is inside the $0.50 session cap; out-of-wallet total
  including escrow credit is exactly $0.50. Any further spend needs a
  fresh explicit approval — never a silent purchase or bridge.

### Worked receipt example (TxLens t01, 6 Nov 2026)

Pick the first served row in the corrected results file — TxLens (9002),
trap `t01-plain-transfer`, tx
`0xd47a090fee50ae43d3af7dcb03eced0be6c98a48b3aa92dc21a8c4d9d784ae96`.
Its base64 `X-TELEGRAPH-RECEIPT` decodes to:

```json
{"receipt_hash": "0x4e97a41ee98c74bde4c2c3bfab22dd1db598761c0367fa70c525899b41bf5626",
 "rail": "x402", "payer": "0x170DfA67D1e37915d8130eaB9bD3b0a4E115f0C0",
 "miner": "5078", "intent": "ONCHAIN_TX_LOOKUP_GENERAL",
 "amount_uusdc": "10000", "epoch_id": 2027, "settlement": "onchain",
 "chain": "eip155:11155111",
 "tx_hash": "0xca5bfa75ae22f984b7d75857bd64e3f364ff68950ed8df77372ccc8a870d9984",
 "timestamp": 1793973868}
```

Reading it: `payer` is burner 3; `amount_uusdc` "10000" is $0.01 (10,000
micro-USDC), matching `cost_usd: 0.01` and the live 402 challenge;
`settlement: "onchain"` on `eip155:11155111` (Ethereum Sepolia); the receipt's
`tx_hash` is the settlement transaction, and it is also recorded as
`receipt_settlement_tx` on the row — verify it on the explorer:
https://sepolia.etherscan.io/tx/0xca5bfa75ae22f984b7d75857bd64e3f364ff68950ed8df77372ccc8a870d9984
The row's `signal_hash` is
`0xc26add9f3e8a05f81a3ea2eeb3e7f1c7218f23f3e261aa6dae3f03f5d1c744b2`.
The answer itself failed the trap (TxLens answered `not_found` for a mined,
confirmed tx) — the receipt proves the call was bought and paid for, not
that the answer was right.

**Receipt miner IDs (observed values):** the `miner` field in the decoded
receipts is `5078` on all 12 TxLens (catalogue 9002) calls and `172` on all
12 Truvian (catalogue 8453) calls. These are the values observed in the
receipts as received, associated by row with the provider whose call the
receipt arrived on. No registry explanation for the mapping is claimed —
the catalogue miner ID and the receipt miner ID are different numbers, and
that is simply what the receipts say. (For example, the Truvian t08 receipt
— the trap whose correction moves Truvian 3/12 → 4/12 — has
`receipt_hash` `0x6a7b751a869cd69d4aae8d740094292fd7a2d98a3315873b8606c110a497850c`,
`miner` `172`, same payer, amount, epoch, and chain as above, and
`tx_hash` `0xf420adde8c02245a3c4917b4f332b0f1524dbd10e933200c9363a80c7584afe3`.)

## 5. Day-1 gates — outcomes (6–8 Nov 2026)

1. **Prize-payment terms published** (rules say before the competition
   opens): **STILL UNPUBLISHED 6 Nov** — UK eligibility, payout
   currency/method, and timing are unverified. Registration alone
   confirms none of these. The submission states this plainly.
2. **Free testnet USDC/gas obtained:** RESOLVED WITHOUT a faucet — no
   Telegraph faucet exists (web, docs, GitHub, Discord checked; organiser
   email 1 Nov unanswered after 5 days). The accepted token
   (`0xcc194e1a843B658526D0D5C431f670028582Ae17`) has an open `mint`
   function; burner 3 self-minted 30 test USDC, as other builders do
   (on-chain: distinct wallets self-minting 1/10/20). Sepolia gas from
   the PoW faucet (0.05284 ETH, 1 Nov). No real money, no purchase.
3. **Competing-provider supply re-confirmed live:** 24 miners in the
   fresh 6 Nov catalogue; 5 providers attempted, 2 served (TxLens 9002,
   Truvian 8453), 3 unservable for this intent (LiveCert 4433, Sigil
   9010, OnChain Intel 900) — see the live results file.
4. **Evaluator submission route** (VERIFIED 8 Nov 2026, Discord #hackathon):
   there is NO sign-in on the hackathon website and none is needed — the
   hackathon is completely open. Sign in on anjoman.ai (Telegraph's
   dashboard) and submit evaluation material at anjoman.ai/dashboard/eval.
   No GitHub bounty issue exists for `ONCHAIN_TX_LOOKUP_GENERAL`, so there
   is nothing to /claim for this intent. The final submission form does NOT
   exist yet — it opens later and will be shared in Discord before the
   1 Dec deadline.

## 6. Honest limits (say these on every surface)

- Testnet use is **not** adoption, and manufactured adoption (e.g. a
  self-purchase counted as a buyer) is a disqualifier. No adoption,
  user, accuracy, or time-saved figure exists for TrapTest yet — do not
  invent one.
- The entry is single-Intent (`ONCHAIN_TX_LOOKUP_GENERAL`); it does not claim
  coverage of other Intents.
- If the live leaderboard UI slips, the fallback is a scored table +
  receipts for the same fixed trap set — same evidence, plainer layout.
- Scores: judging is /100 (Technical 35, min 24; Commercial 30;
  Adoption 15; Integration 10; Proof 10; need 70+). TrapTest's honest
  ceiling on Adoption is low (see above); its case rests on Technical,
  Integration, and Proof.
- Schema gaps are not lies: Truvian returns no `status` for confirmed
  transactions (its block/from/to/value were all correct on 6 such
  traps) — those traps score FAIL under the strict rules (a missing
  field is a failure), and the gap is reported as a gap, not as a wrong
  answer. TxLens's `not_found` answers ARE wrong answers (the txs are
  mined and confirmed), not a schema gap.
- Failed calls can still settle: Sigil and OnChain Intel failed every
  call, yet $0.01 per call settled on-chain into Telegraph escrow
  credit (not billed). The run log records this per row
  (`escrow_credit_usd`) and in the totals — a reviewer checking the
  burner balance against billed cost will find the $0.24 difference
  explained, not hidden.

## 7. Mainnet readiness

TrapTest uses the same Direct Ask flow on mainnet as on testnet: the Engine
and contract addresses are parameters, not hardcoded testnet values, and
there are no testnet-only shortcuts in the scoring path — the same strict
scorer, frozen trap discipline, and receipt verification apply. Moving to
mainnet changes only the funding (real USDC instead of self-minted test
USDC) and the trap set (mainnet transactions with ground truth checked
against public chain data); no code change to the buy–score–rank loop is
needed. No mainnet run has been made and none is claimed.
