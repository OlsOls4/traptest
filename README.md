# TrapTest — live build (6 Nov 2026, corrected re-score 8 Nov 2026)

**Status: LIVE RUN COMPLETE 6 Nov 2026, corrected re-score 8 Nov 2026.
Registered 27 Oct 2026 (Olly McBride, Individual, Discord ols0817, project
TrapTest). 12 frozen traps × 5 providers = 60 scored rows, all event-period
(1 Nov–1 Dec 2026), in `results-live/full-run-2026-11-06.json`
(`data_kind: LIVE`, strict original) and
`results-live/results-corrected-2026-11-08.json`
(`data_kind: CORRECTED_REANALYSIS`), rendered at `docs/leaderboard/`.
Corrected: Truvian 8453 — 4/12, TxLens 9002 — 2/12, LiveCert 4433 / Sigil
9010 / OnChain Intel 900 — 0/12 served (unservable). Billed $0.26 total
including $0.02 smoke tests ($0.24 in the run file + $0.02 smoke); $0.24
settled into Telegraph escrow credit, NOT billed; wallet 30.00 → 29.50 test
USDC. Demo video v2 (2026-11-08) in
`docs/demo-video/traptest-demo-2026-11-08.mp4` — DONE 8 Nov 2026, 2:42 (161.6 s), 1280×720.**

**In 60 seconds:** TrapTest is a lie-detector for Telegraph's intelligence
market. It buys fixed trap transaction queries — queries whose correct answer
is known in advance — from competing providers on testnet, scores each answer
pass/fail against the truth, and publishes the result as a live leaderboard.
A provider that returns a stale or wrong answer is shown failing, with its
receipt, so builders choosing a provider can see whose answers can be
trusted — not just who is ranked first.

**Submission status:**
- Submitted: evaluation material admitted on Anjoman 8 Nov 11:20–11:21 (12 preference pairs + 1 truth source; pool went 4 → 5 contributors, activation threshold met). Final project submission form does not exist yet — it opens later and will be shared in Discord before the 1 Dec deadline.
- Done and ready: live run (60 rows), corrected re-score, leaderboard page,
  how-to-run, submission pack, evaluation material for Anjoman
  (`anjoman-material/`), demo video v2 (2026-11-08, 2:42).
- Not yet: final submission form (does
  not exist yet — it opens later and will be shared in Discord before the
  1 Dec deadline); repo push state (live-build files not yet confirmed
  pushed — open item, see submission pack).
- Next step: apply the staged Anjoman pair fixes (t04/t06/t10) and re-submit;
  confirm repo push state; watch Discord for the final submission form.

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
- Judging: /100, Technical 35 (min 24), Commercial 30, Adoption 15,
  Integration 10, Proof 10; need 70+.
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
  wallet 30.00 → 29.50 test USDC (drop $0.50 incl. $0.02 smoke tests).
  All 24 served receipts verified on-chain.
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
call):

```bash
python3 scripts/full_run.py   # 12 frozen traps × TxLens (9002) + LiveCert (4433)
python3 scripts/mini_run.py   # 12 frozen traps × Sigil (9010) → OnChain Intel (900) → Truvian (8453)
```

Both scripts read the FROZEN trap set (`traps-frozen-2026-11-06.json`, never
edited), buy via Direct Ask with the x402 provider, score with
`traptest/scoring.py`, and append to `results-live/full-run-2026-11-06.json`
(`data_kind: LIVE`). The leaderboard renders the corrected re-score
(`results-live/results-corrected-2026-11-08.json`, copied to
`docs/leaderboard/results.json`).

## Run prep tests

```
python3 -m unittest discover -s tests -v
```
