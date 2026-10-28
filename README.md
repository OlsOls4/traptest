# TrapTest — prep scaffold (27 Oct 2026)

**Status: REGISTERED 27 Oct 2026 (Olly McBride, Individual, Discord ols0817, project TrapTest). PREP ONLY until 1 Nov: no Telegraph event purchase has been made and no event evidence exists yet.**

TrapTest (Telegraph Hackathon Season II, Evaluator-led): trap queries with known
ground truth are bought from competing transaction-intelligence providers on
testnet, scored pass/fail against the truth, and published as a live leaderboard.

## Truth list (freeze before submission, per hackathon_submission_check skill)

- Hackathon: Telegraph Season II, 1 Nov–1 Dec 2026, deadline 1 Dec 23:59 UTC.
- Primary intent: `ONCHAIN_TX_LOOKUP` (23 miners live on the Engine at
  verification on 27 Oct 2026; re-fetch at run time — miner IDs are NOT stable,
  never hardcode them).
- Purchase flow: Direct Ask `POST /engine/v1/ask/{minerId}` (auto-routed ask
  picks one miner and cannot be used to compare competitors). Price is read
  from the live 402 challenge, never from the catalogue `cost_per_call` field.
- Evidence per served call: `cost_usd`, `signal_hash`, Telegraph receipt
  (`X-TELEGRAPH-RECEIPT`).
- Judging: /100, Technical 35 (min 24), Commercial 30, Adoption 15,
  Integration 10, Proof 10; need 70+.

## Gates (27 Oct 2026)

- Provider supply: VERIFIED (see IDEATION.md verification section).
- Entry fee: site says "free to register" (live browser check 27 Oct).
- Prize-payment terms (UK eligibility, payout currency/method/timing):
  UNVERIFIED — rules say they must be available before the competition opens
  (1 Nov); re-check on/after 1 Nov.
- Free Base Sepolia testnet USDC/gas acquisition: UNVERIFIED — no Telegraph
  source documents a faucet. Day-1 action: faucet claim into a burner wallet,
  confirm balance at Telegraph's USDC contract, before any TrapTest code that
  spends. A failed claim is a stop, not a reason to buy/bridge with real money.
- Registration: COMPLETED 27 Oct 2026 — Olly McBride, Individual, Discord ols0817, project TrapTest, email ollymcbride4@gmail.com verified. Confirmation "You're registered", no reference number shown.

## Prep rules

- Code written before 1 Nov is framework only: trap schema, scoring,
  leaderboard aggregation, provider-client interface, tests with MOCK
  fixtures. H2-specific activity and transaction evidence must come from the
  event period (1 Nov–1 Dec) — mock fixtures in tests are NEVER event
  evidence and must never be submitted as real results.
- Zero-cost (conditional): online/testnet only, no travel, local deterministic
  scoring, no paid model/API/dataset/GPU/hosting. Per-call spend is in Base
  Sepolia testnet USDC (~$0.01/call per docs, plus 2% protocol fee), capped by
  a small fixed trap set — conditional on free testnet USDC acquisition (above).

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
- `tests/` — stdlib unittest, mock fixtures only.
- `docs/leaderboard/` — zero-cost static leaderboard page (`index.html`,
  renders `results.json`; shipped file is MOCK-labelled prep data only).
- `docs/how-to-run.md` — reviewer guide: judge-in-60-seconds path,
  reproduction checklist, day-1 gates.
- `docs/submission-pack.md` — submission skeleton: frozen truth list,
  public/commercial summary drafts, submission-check steps, live gaps. `test_providers.py`
  (mocked transport, no network) and `test_run.py` (gate behaviour).

## Run prep tests

```
python3 -m unittest discover -s tests -v
```
