# TrapTest — live build (6 Nov 2026, corrected re-score 8 Nov 2026)

**In 60 seconds:** TrapTest is a lie-detector for Telegraph's intelligence
market. It buys fixed trap transaction queries — queries whose correct answer
is known in advance — from competing providers on testnet, scores each answer
pass/fail against the truth, and publishes the result as a live leaderboard.
A provider that returns a stale or wrong answer is shown failing, with its
receipt, so builders choosing a provider can see whose answers can be
trusted — not just who is ranked first.

**Results:**
- Expansion set (9 Nov 2026, t13–t24, scoring v2): ChainWire 1707307 — 11/12 (field accuracy 46/47).
- Frozen set (6 Nov 2026, corrected re-score 8 Nov): Truvian 8453 — 4/12, TxLens 9002 — 2/12.
- Leaderboard: `docs/leaderboard/` (live at https://olsols4.github.io/traptest/docs/leaderboard/) · Demo video v3.2: https://youtu.be/5o46sCyNeqo (3:08; v3.1 at https://youtu.be/z7mHzCqG1JQ, v3 at https://youtu.be/XB9LljuT9Ck, v2 at https://youtu.be/993JOD3JRXs).

**Next step:**
- Open the leaderboard (`docs/leaderboard/`, or the live link above) and check both ranked tables and both verdicts.
- Verify in 60 seconds with no spend: the checks in `docs/how-to-run.md` §2 (165 tests + the static leaderboard page).
- One-trap dry-run (validates traps, key, providers and output path; spends and writes nothing): `python3 -m traptest.run --traps traps-replay-2026-11-08.json --providers 9002,8453 --key .burner-replay.key --out results-live/replay-2026-11-08.json --dry-run`

**New in the repo (13 Nov 2026):**
- Starter kit — reuse the trap format on a new intent: `starter-kit/` (template + worked example; the example files are teaching examples only — never submit them to Anjoman as real material).
- How to evaluate a tx-intelligence provider: `docs/how-to-evaluate-a-provider.md` — the method, the strict scoring rules, and the escrow and x402 payment findings.
- Provider fix guides: `docs/provider-fix-guides/` — what Truvian, TxLens and ChainWire would need to change to improve their scores, each with a dated re-run offer.

## Build log (13 Nov 2026)

**Status: LIVE RUN COMPLETE 6 Nov 2026, corrected re-score 8 Nov 2026,
re-run 8 Nov 2026 (24 calls, $0.24, scores stable); expansion clean re-run
9 Nov 2026 (36 calls, $0.36, 36/36 receipts verified). Repo PUBLIC
(https://github.com/OlsOls4/traptest, head 5ba71220, 9 Nov 17:13Z).
Registered 27 Oct 2026 (Olly McBride, Individual, Discord ols0817, project
TrapTest). 24 frozen traps (12 on 6 Nov + 12 expansion on 9 Nov), all
event-period (1 Nov–1 Dec 2026): frozen set 12 traps × 5 providers =
60 scored rows in `results-live/full-run-2026-11-06.json`
(`data_kind: LIVE`, strict original) and
`results-live/results-corrected-2026-11-08.json`
(`data_kind: CORRECTED_REANALYSIS`), rendered at `docs/leaderboard/`.
Corrected: Truvian 8453 — 4/12, TxLens 9002 — 2/12, LiveCert 4433 / Sigil
9010 / OnChain Intel 900 — 0/12 served (unservable). Billed $0.50 on 6–8 Nov
($0.26 on 6 Nov incl. $0.02 smoke + $0.24 re-run 8 Nov); $0.24 settled
into Telegraph escrow credit, NOT billed. Expansion 9 Nov: $0.42 task spend
+ $0.36 clean re-run. Wallet 30.00 → 28.48 test USDC (cumulative drop
$1.52: $1.25 billed + $0.27 escrow credit).
Demo video v3.2 (2026-11-13) PUBLIC at https://youtu.be/5o46sCyNeqo —
3:08 (188.1 s), 1280×720 — v3.1 re-rendered at natural speed, never slowed
(v3.1, 2026-11-13, at https://youtu.be/z7mHzCqG1JQ; v3 at
https://youtu.be/XB9LljuT9Ck; v2, 2026-11-08, at https://youtu.be/993JOD3JRXs,
audio approved by the user). Anjoman evaluation
material ADMITTED 8 Nov 11:20–11:21 (12 preference pairs + 1 truth source);
rollover VERIFIED 8 Nov 17:36 — all 13 rows eligible (pool 702 rows,
5 eligible submitters at that snapshot). Expansion pairs UPLOADED 9 Nov
17:09 (browser): 12 stored, 0 already there, 0 refused; Admitted ·12 new;
pool 1,045 → 1,057 rows from 6 contributors. Live pool API 13 Nov: 898
eligible, 1,057 total, 6 submitters (eligible_submitters 6). A signed-in
dashboard re-check is still pending to confirm the 12 expansion rows'
admitted-vs-eligible state. Bounties repo starred. X posts 1–3 all LIVE
(posted by the user himself: post 1, 8 Nov
https://x.com/OlsOls4/status/2119431200389447911; post 2, 12 Nov
https://x.com/OlsOls4/status/2121001361965789577; post 3, 12 Nov);
milestone post scheduled 14 Nov 09:00 GMT (revised draft approved 13 Nov).
Final submission form still does not exist — it opens later and will be
shared in Discord before the 1 Dec deadline.**

**Submission status (13 Nov 2026):**
- Submitted: evaluation material admitted on Anjoman 8 Nov 11:20–11:21 (12 preference pairs + 1 truth source; pool went 4 → 5 contributors, activation threshold met). Rollover verified 8 Nov 17:36 — all 13 rows eligible (pool 702 rows, 5 eligible submitters at that snapshot). Expansion pairs uploaded 9 Nov 17:09 (browser): 12 stored, 0 already there, 0 refused; Admitted ·12 new; pool 1,045 → 1,057 rows from 6 contributors. Live pool API 13 Nov: 898 eligible, 1,057 total, 6 submitters. A signed-in dashboard re-check 13 Nov confirmed all 12 expansion pairs eligible (Eligible ·25 total: 13 original + 12 expansion). Final project submission form does not exist yet — it opens later and will be shared in Discord before the 1 Dec deadline.
- Done and ready: live run (60 rows), corrected re-score, 8 Nov re-run (24 calls, scores stable), expansion clean re-run 9 Nov (36 calls, $0.36, 36/36 receipts verified), leaderboard page (both sets pre-rendered), how-to-run, submission pack, evaluation material for Anjoman (`anjoman-material/`; 24 preference pairs + 1 truth source submitted), demo video v3.2 PUBLIC (https://youtu.be/5o46sCyNeqo; v3.1 at https://youtu.be/z7mHzCqG1JQ, v3 at https://youtu.be/XB9LljuT9Ck, v2 at https://youtu.be/993JOD3JRXs), repo public (main branch), bounties repo starred, X posts 1–3 all live (posted by the user himself 8 + 12 Nov).
- Not yet: final submission form (does not exist yet — it opens later and will be shared in Discord before the 1 Dec deadline); milestone post (scheduled 14 Nov 09:00 GMT, revised draft approved 13 Nov).
- Next step: the staged Anjoman pair fixes (t04/t06/t10) were re-uploaded 8 Nov 11:38 and did NOT take — the corrected rows went to a superseded-duplicates bucket and the original weaker pairs remain in effect (no replace control on the eval page; asking the organisers is the only route if replacement matters). Watch Discord for the final submission form.
- Expansion set DONE 9 Nov 2026 (t13–t24, scoring v2, separate leaderboard section): ChainWire 1707307 — 11/12 (field 46/47); Truvian 8453 — 2/12 (field 39/49); TxLens 9002 — 2/12 (field 2/47); Verity 9001 / INTERLOCK 9007 unservable; ChainWire 7317307 / 7307 t13-pass probes only. Combined 24-trap (NOT one uniform measure): Truvian 6/24, TxLens 4/24. Expansion task spend $0.42 (cap $0.50); clean re-run $0.36; wallet 28.84 → 28.48 test USDC after the clean re-run (cumulative 30.00 → 28.48, drop $1.52: $1.25 billed + $0.27 escrow credit). Expansion pairs uploaded to Anjoman 9 Nov 17:09 (browser), 12 stored / 0 already there / 0 refused; Admitted ·12 new.

TrapTest (Telegraph Hackathon Season II, Evaluator-led): trap queries with known
ground truth are bought from competing transaction-intelligence providers on
testnet, scored pass/fail against the truth, and published as a live leaderboard.

## Truth list (freeze before submission, per hackathon_submission_check skill)

- Hackathon: Telegraph Season II, 1 Nov–1 Dec 2026, deadline 1 Dec 23:59 UTC.
- Primary intent: `ONCHAIN_TX_LOOKUP_GENERAL` (21 miners live on the Engine at
  verification on 1 Nov 2026; re-fetch at run time — miner IDs are NOT stable,
  never hardcode them).
- Purchase flow: Direct Ask `POST /engine/v1/ask/{minerId}` (auto-routed ask
  picks one miner and cannot be used to compare competitors). Price is read
  from the live 402 challenge, never from the catalogue `cost_per_call` field.
- Evidence per served call: `cost_usd`, `signal_hash`, Telegraph receipt
  (`X-TELEGRAPH-RECEIPT`).
- Judging (TRACK 03 Evaluator rubric, verified live 8 Nov 2026): /100 —
  Measurement validity 40 (minimum 28/40 to qualify), Integrity and
  robustness 15, Reproducibility and protocol compatibility 10, Useful
  evaluation coverage and demonstrated improvement 10, Documentation and
  integration clarity 5, Organic growth / education / developer activation
  20 (5+5+5+5); need 70/100 AND pass 28/40 on Measurement validity.
- Live results (6 Nov 2026, frozen trap set `traps-frozen-2026-11-06.json`,
  frozen 13:59 UTC; corrected re-score 8 Nov 2026 in
  `results-live/results-corrected-2026-11-08.json`): Truvian 8453 — 4/12
  (t07, t08, t11, t12; field accuracy 37/47; strict original 3/12, 36/47 —
  only t08 changed, under the fixed normaliser); TxLens 9002 — 2/12 (field
  accuracy 2/47); LiveCert 4433 — 0/12 served (503 no_compatible_miner);
  Sigil 9010 — 0/12 served (HTTP 500 upstream 404); OnChain Intel 900 —
  0/12 served (HTTP 500 upstream 400, "Could not determine a supported
  chain"). The three unserved providers are an UNSERVABLE tier, not a 0%
  pass rate. Truvian 4/12 vs TxLens 2/12 differ by two traps on n=12 —
  treat a small margin as evidence, not a proven gap. Billed $0.26 total
  including $0.02 smoke tests ($0.24 in the run file + $0.02 smoke);
  $0.24 settled into Telegraph escrow credit, not billed (Sigil + OnChain
  Intel, $0.12 each — failed calls that still settled); burner 3
  wallet 30.00 → 29.26 test USDC (cumulative drop $0.74: $0.50 billed —
  $0.26 on 6 Nov incl. $0.02 smoke + $0.24 re-run 8 Nov — plus $0.24
  escrow credit). 8 Nov re-run (`results-live/replay-2026-11-08.json`):
  24 calls, $0.24, scores stable (Truvian 4/12, TxLens 2/12), wallet
  29.50 → 29.26.
  All 24 served receipts verified on-chain (backfilled 13 Nov 2026:
  the flags were null in the file until re-verified on-chain — see
  `receipt_backfill` in `results-live/replay-2026-11-08.json`).
- Expansion set (9 Nov 2026, `traps-frozen-2026-11-09.json`, frozen
  13:07:38 UTC, SHA-256
  `940a00400477e0aefb38afe1da20fb98cc03b187e7218da252d322fd4699b5ba`,
  ADDITIVE — the frozen 12 are untouched): 2 traps per category,
  t13–t24, under scoring v2 (disclosed, never retroactive): token
  traps score the NATIVE tx value (0 wei for t13/t14, scored
  explicitly — the frozen t03/t04 scored the Transfer-event amount,
  which no provider returns in `value`); unknown traps carry the
  strict-unknown rule (a `not_found` answer with any invented
  from/to/value/block fails outright); field-weighted accuracy is a
  co-primary metric alongside pass rate. Results (36 served rows in
  `docs/leaderboard/results-expansion.json`, all receipts verified
  on-chain): ChainWire 1707307 (Cross-Checked) — 11/12 (field accuracy
  46/47; only t17 fails — reverted tx value returned 0, expected
  607000000000000 wei); Truvian 8453 — 2/12 (t17, t18; field 39/49);
  TxLens 9002 — 2/12 (t23, t24 only; field 2/47). Truvian's t23/t24
  fail ONLY under the v2 rule, on its `from` source label ("Truvian
  onchain lookup over public JSON-RPC") — a provenance string, not a
  hallucinated sender address; reported as a schema-convention
  artefact. Verity 9001 (HTTP 500 upstream 404) and INTERLOCK 9007
  (HTTP 503 `no_compatible_miner`) served 0 — unservable. ChainWire
  7317307 / 7307 each served and passed the t13 probe only (full sets
  not run — the task's $0.50 cap allowed one full new-miner set, run
  on 1707307); not ranked on 1 trap. Combined 24-trap numbers
  (frozen 12 + expansion 12) are NOT one uniform measure (different
  semantics per set): Truvian 6/24 (field 76/96), TxLens 4/24 (field
  4/94); ChainWire ran the expansion set only. Providers diverge on
  ≥3 traps on the expansion set (TxLens vs Truvian: 4; ChainWire vs
  either incumbent: 9). Expansion task spend $0.42 total (hard cap
  $0.50): $0.24 expansion run + $0.12 ChainWire 1707307 full set +
  $0.03 probes billed + $0.03 Verity escrow credit (failed calls that
  still settled); wallet 29.26 → 28.84 test USDC. The 7 cap-skipped
  rows in the expansion run file (1707307 t18–t24, file-cumulative
  cap) are excluded from scoring; the 7 bought rows are in
  `results-live/expansion-run-1707307-rest-2026-11-09.json`. The 12
  expansion pairs were uploaded to Anjoman 9 Nov 17:09 (browser),
  12 stored / 0 already there / 0 refused; Admitted ·12 new. The clean
  re-run (36 calls, $0.36) took the wallet 28.84 → 28.48 test USDC;
  cumulative 30.00 → 28.48 (drop $1.52: $1.25 billed + $0.27 escrow
  credit). Tests: 165, all passing (`python3 -m unittest discover
  -s tests`, 13 Nov 2026).
- Comparator WASM: KILLED with evidence 9 Nov 2026 — see
  `docs/comparator-wasm-kill.md` (one-integer scoring cannot express
  multi-field strict scoring; generic fallback already scores the
  intent; activation blocked by platform bug #171; Sireadell reg 118
  pending since 3 Nov).
- Ground truth re-checked 9 Nov 2026 against a SECOND public Base
  Sepolia RPC (`https://sepolia.base.org`, not the freeze-time source):
  22/24 txs match the frozen ground truth on every scored field —
  see `results-live/ground-truth-recheck-2026-11-09.json`. The two
  exceptions (t03/t04) differ on `value` only because the frozen file
  records the Transfer-event amount (documented v1 flaw), while the
  native tx value is 0; the second RPC's own receipts confirm the
  frozen event amounts exactly (950000 and 2000000000000000000).
- Payment: Direct Ask 402, $0.01/call, settlement Ethereum Sepolia
  (eip155:11155111), accepted token `0xcc194e1a843B658526D0D5C431f670028582Ae17`
  ("USD Coin") — NOT Circle faucet USDC. The token has an open mint
  (self-mint, as other builders do); no Telegraph faucet exists. Gas:
  Sepolia ETH from the PoW faucet (sepolia-faucet.pk910.de). Zero real money.

## Intent migration note — 1 Nov 2026

- Old intent `ONCHAIN_TX_LOOKUP`: 0 miners on 1 Nov 2026
  (`/engine/v1/intents/ONCHAIN_TX_LOOKUP/miners` returned
  `{"count":0,"miners":[]}`) — the prep default was stale and is no longer
  usable.
- New intent `ONCHAIN_TX_LOOKUP_GENERAL`: 21 miners on 1 Nov 2026
  (~10 usable-looking by catalogue description after excluding
  Blockscout list-only endpoints and VulnFeed; catalogue presence is
  not a live probe, and no provider is scored until it answers a
  Direct Ask).
- Migrated 1 Nov 2026 across code (`traptest/run.py` `--intent`
  default, `traptest/trap_catalog.py` `INTENT` constant and validation,
  `traptest/traps.py` docstring), tests (intent constants/fixtures in
  `test_providers.py`, `test_scoring.py`, `test_trap_catalog.py` — these
  tests hardcoded the old intent, so they were updated to the new one;
  no test logic was weakened), and docs (README truth list, `docs/
  how-to-run.md`, `docs/submission-pack.md` truth list, `traptest/
  trap_design.md`, `docs/demo-script.md`). Dated historical records
  (`docs/supply-recheck-2026-10-28.md`, `docs/judge-review.md`) were
  deliberately left untouched. Other catalogue rules are unchanged:
  30-trap cap, mandatory reverted + unknown categories, provenance
  validation.

## Gates (27 Oct 2026; outcomes 6 Nov 2026)

- Provider supply: VERIFIED (see IDEATION.md verification section).
- Entry fee: site says "free to register" (live browser check 27 Oct).
- Prize-payment terms (UK eligibility, payout currency/method/timing):
  STILL UNVERIFIED 6 Nov — rules say they must be available before the
  competition opens (1 Nov); re-checked 1 Nov and 6 Nov, still
  unpublished. State this plainly in the submission; do not claim a UK
  payout.
- Free testnet USDC/gas acquisition: RESOLVED 6 Nov WITHOUT a faucet —
  no Telegraph faucet exists (web/docs/GitHub/Discord checked). The
  accepted token (`0xcc19…`) has an open mint; burner 3 self-minted 30
  test USDC (other builders self-mint 1/10/20 the same way). Sepolia gas
  from the PoW faucet (0.05284 ETH, 1 Nov). Zero real money, no purchase
  or bridge.
- Registration: COMPLETED 27 Oct 2026 — Olly McBride, Individual, Discord ols0817, project TrapTest, email ollymcbride4@gmail.com verified. Confirmation "You're registered", no reference number shown.
- Submission route (VERIFIED 8 Nov 2026, Discord #hackathon): there is NO
  sign-in on the hackathon website and none is needed — the hackathon is
  completely open. Sign in on anjoman.ai (Telegraph's dashboard) and submit
  evaluation material at anjoman.ai/dashboard/eval. No GitHub bounty issue
  exists for `ONCHAIN_TX_LOOKUP_GENERAL`, so there is nothing to /claim for
  this intent. The final submission form does NOT exist yet — it opens later
  and will be shared in Discord before the 1 Dec deadline.

## Prep rules

- Code written before 1 Nov is framework only: trap schema, scoring,
  leaderboard aggregation, provider-client interface, tests with MOCK
  fixtures. H2-specific activity and transaction evidence must come from the
  event period (1 Nov–1 Dec) — mock fixtures in tests are NEVER event
  evidence and must never be submitted as real results.
- Zero-cost (conditional): online/testnet only, no travel, local deterministic
  scoring, no paid model/API/dataset/GPU/hosting. Per-call spend is in
  Telegraph's accepted test USDC on Ethereum Sepolia
  (`0xcc194e1a843B658526D0D5C431f670028582Ae17`, self-minted via its open
  mint, $0.01/call), capped by the frozen 12-trap set — see the live
  results in the truth list above. No real money was spent.

## Layout

- `traptest/traps.py` — trap definition + validation.
- `traptest/scoring.py` — deterministic pass/fail scoring vs ground truth.
- `traptest/leaderboard.py` — per-provider aggregation + ranking.
- `traptest/providers.py` — provider-client interface + live catalogue fetch
  + Direct Ask client (fresh catalogue check, 402 handling, receipt/cost
  capture; payment execution delegated to a caller-supplied payment
  provider — no wallet/keys in prep; see module docstring).
- `traptest/run.py` — gated live runner: refuses (exit 2, no network call)
  unless UTC date ≥ 2026-11-01 AND `./LIVE-ACTIVATED` marker exists.
  Even gated, it buys nothing without a trap set + payment provider.
- `tests/` — stdlib unittest, mock fixtures only (`test_providers.py`:
  mocked transport, no network; `test_run.py`: gate behaviour).
- `docs/leaderboard/` — zero-cost static leaderboard page (`index.html`,
  renders `results.json`; shipped file is the corrected re-analysis of the
  6 Nov 2026 LIVE run, 60 rows — corrected Truvian 4/12, TxLens 2/12, strict
  original preserved alongside).
- `docs/how-to-run.md` — reviewer guide: judge-in-60-seconds path,
  reproduction checklist, day-1 gates (with 6–8 Nov outcomes).
- `docs/demo-video/` — demo video v2 (2026-11-08, 2:42; v1
  2:36 local file superseded), narration script + storyboard, build script.
- `scripts/full_run.py` — full scored run (12 traps × TxLens + LiveCert).
- `scripts/mini_run.py` — second-provider mini-run (Sigil → OnChain
  Intel → Truvian, fresh catalogue, escrow-aware accounting).
- `docs/submission-pack.md` — submission skeleton: frozen truth list,
  public/commercial summary drafts, submission-check steps, live gaps.

## Replay the run (reviewer commands)

From the repo root, with your own burner funded as in
`docs/how-to-run.md` §1 (these buy traps on testnet at $0.01 per served
call; the per-run hard spend cap defaults to $0.30 — see
`traptest/run.py` `DEFAULT_SPEND_CAP_USD`). Validate first without
spending or writing anything, with the parametrised runner:

```bash
python3 -m traptest.run --traps traps-frozen-2026-11-06.json \
    --providers 9002,8453 --out results-live/replay-<date>.json --dry-run
```

Then run it (same command without `--dry-run`). The historical
6 Nov scripts replay the same shapes but now REQUIRE `--out` pointing
at a NEW file — they refuse the frozen results file and refuse an
`--out` that already exists (and they have no `--dry-run` flag; use
the parametrised runner above to dry-run):

```bash
python3 scripts/full_run.py --out results-live/full-replay.json   # 12 frozen traps × TxLens (9002) + LiveCert (4433)
python3 scripts/mini_run.py --out results-live/mini-replay.json   # 12 frozen traps × Sigil (9010) → OnChain Intel (900) → Truvian (8453)
```

Both scripts read the FROZEN trap set (`traps-frozen-2026-11-06.json`, never
edited), buy via Direct Ask with the x402 provider, score with
`traptest/scoring.py`, and write `data_kind: LIVE` rows to the NEW
`--out` file (never to the frozen 6 Nov file). The leaderboard renders
the corrected re-score
(`results-live/results-corrected-2026-11-08.json`, copied to
`docs/leaderboard/results.json`).

## Run prep tests

```
python3 -m unittest discover -s tests -v
```
