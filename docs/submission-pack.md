# TrapTest — submission pack (live, 6 Nov 2026)

**Status: LIVE RUN COMPLETE 6 Nov 2026, corrected re-score 8 Nov 2026, not
yet submitted. Every number below is event-period (1 Nov–1 Dec 2026)
evidence from `results-live/full-run-2026-11-06.json` (60 rows,
`data_kind: LIVE`, strict original) and
`results-live/results-corrected-2026-11-08.json` (corrected re-score).
No [BRACKET] below may be filled with a mock, estimated, or pre-window
number — all remaining brackets are genuine gaps (repo-public state,
prize terms).

## 1. Truth list (freeze before the final polish round)

Derived from its own source, not copied from another document. Any number
not on this list is unverified and must not appear on a submission surface.

| Item | Value | Source |
|---|---|---|
| Hackathon / window / deadline | Telegraph Season II, 1 Nov–1 Dec 2026, deadline 1 Dec 23:59 UTC | hackathon.telegraphprotocol.com (rules/timeline, read 27 Oct) |
| First integration milestone | 14 Nov 2026 (progress check only, not disqualification) | Same |
| Registration | COMPLETED 27 Oct 2026: Olly McBride, Individual, Discord ols0817, project TrapTest (Python), email ollymcbride4@gmail.com verified; confirmation "You're registered", no reference number shown | Live browser registration, 27 Oct |
| Primary intent | `ONCHAIN_TX_LOOKUP_GENERAL` | Engine catalogue, 1 Nov 2026 check: 21 miners listed (see migration row below) |
| Provider supply at check | 23 miners listed, ≥10 usable after filtering list-only endpoints | Engine `/intents/ONCHAIN_TX_LOOKUP/miners`, 27 Oct — **re-fetch at run time; miner ids are not stable** |
| Provider supply re-check | 23 listed, 12 usable-looking by catalogue description (10 Blockscout list-only excluded; VulnFeed excluded as contract-security, not tx-hash lookup) — catalogue presence only, NOT a live probe | Same endpoint, 28 Oct — see `docs/supply-recheck-2026-10-28.md`. Re-fetch again at run time; pre-flight ≥2–3 providers before freezing the trap set |
| Intent migration (1 Nov 2026) | Old intent `ONCHAIN_TX_LOOKUP`: 0 miners on 1 Nov; successor `ONCHAIN_TX_LOOKUP_GENERAL`: 21 miners, ~10 usable-looking by description — code, tests and docs migrated to the new intent 1 Nov (see README migration note); the 27/28 Oct rows above are dated history under the old intent | Engine `/intents/ONCHAIN_TX_LOOKUP/miners` and `/intents/ONCHAIN_TX_LOOKUP_GENERAL/miners`, 1 Nov — **re-fetch at run time; miner ids are not stable** |
| Purchase flow | Direct Ask `POST /engine/v1/ask/{minerId}`; price from live 402 challenge, never catalogue `cost_per_call: "0.00"` | docs.telegraphprotocol.com |
| Evidence per served call | `cost_usd`, `signal_hash`, `X-TELEGRAPH-RECEIPT` | Same |
| Testnet | Trap queries are Base Sepolia txs (chain 84532). Payment settles on Ethereum Sepolia (eip155:11155111); accepted token `0xcc194e1a843B658526D0D5C431f670028582Ae17` ("USD Coin", open mint, self-minted — NOT Circle faucet USDC `0x1c7d…`). Engine `https://devnode.telegraphprotocol.com/engine` | Docs + live 402 challenges + on-chain verification, 1–6 Nov 2026 |
| Judging | /100: Technical 35 (min 24), Commercial 30, Adoption 15, Integration 10, Proof 10; need 70+ | Official rules |
| Prize context | $10,000 programme total; main $7,000 (Apps & Agents $3,000, Miners $2,000, Evaluators $2,000) + $3,000 December challenges. TrapTest is Evaluator-led — do not claim the $10,000 or the $3,000 Apps slice as its prize | Official rules |
| Entry fee | Site says "free to register" (27 Oct) | Live browser |
| Test count | 91 tests, all passing (`python3 -m unittest discover -s tests`, 8 Nov 2026) | Repo tests |
| Live results (corrected) | 12 frozen traps × 5 providers = 60 rows, 6 Nov 2026 run, corrected re-score 8 Nov 2026. Corrected: Truvian 8453: 4/12 (t07, t08, t11, t12; field accuracy 37/47). TxLens 9002: 2/12 (t11 + t12 only; field accuracy 2/47). LiveCert 4433: 0/12 served (503). Sigil 9010: 0/12 served (HTTP 500 upstream 404). OnChain Intel 900: 0/12 served (HTTP 500 upstream 400). Strict original (preserved verbatim in the corrected file): Truvian 3/12, field accuracy 36/47 — only t08 changed. Billed $0.26 total including $0.02 smoke tests ($0.24 in the run file + $0.02 smoke); $0.24 settled into Telegraph escrow credit, NOT billed; burner 30.00 → 29.50 test USDC (drop $0.50). 24 served receipts verified on-chain. | `results-live/results-corrected-2026-11-08.json` (CORRECTED_REANALYSIS), `results-live/full-run-2026-11-06.json` (LIVE, strict original), `docs/leaderboard/results.json` (copy of the corrected file) |
| Demo video | v2, 2026-11-08, `docs/demo-video/traptest-demo-2026-11-08.mp4` — DONE, 2:42 (161.6 s), 1280×720; v1 (2:36, 155.8 s, 1280×720, local file `docs/demo-video/traptest-demo-2026-11-06.mp4`) superseded as the submission video. NOT uploaded anywhere. Narration script + storyboard in `docs/demo-video/narration.md`. | Submission |
| Repo | https://github.com/OlsOls4/traptest — [PUBLIC/PRIVATE STATE AT SUBMISSION TO CONFIRM: prep pushed 1 Nov (commit 30b3f8f); live-build files NOT yet pushed — do not submit until the push state is confirmed] | GitHub |
| **UNVERIFIED — do not claim** | UK prize eligibility; payout currency/method/timing (re-checked 1 Nov and 6 Nov, still unpublished) | Re-check before submitting |
| Evaluator submission route (VERIFIED 8 Nov, Discord #hackathon) | There is NO sign-in on the hackathon website and none is needed — the hackathon is completely open. Sign in on anjoman.ai (Telegraph's dashboard). Evaluation material is submitted at anjoman.ai/dashboard/eval. No GitHub bounty issue exists for `ONCHAIN_TX_LOOKUP_GENERAL`, so there is nothing to /claim for this intent. The final submission form does NOT exist yet — it opens later and will be shared in Discord before the 1 Dec deadline. | Discord server findings, 8 Nov 2026 (`~/workspace/goals/traptest-telegraph-season-ii-submission/hidden_files/discord-server-findings-2026-11-08.md`) |

## 2. Short public summary (draft — final wording frozen with the truth list)

> TrapTest is a lie-detector for Telegraph's intelligence market. It buys
> fixed trap transaction queries — queries whose correct answer is known
> in advance — from competing providers on testnet, scores each answer
> pass/fail against the truth, and publishes the result as a live
> leaderboard that re-ranks providers. A provider that returns a stale or
> wrong answer is shown failing, with its receipt, so builders choosing a
> provider can see whose answers can be trusted — not just who is
> ranked first.
>
> Testnet evaluation only. No independent adoption is claimed: all usage
> to date is testnet evaluation by the author during the event window.
> Testnet use is not adoption.

## 3. Commercial summary (draft — numbers only from live evidence)

- **Headline finding: failed calls still settled $0.01 into escrow — $0.24 on
  24 failed calls — buyers pay for failures.** Sigil (9010) and OnChain Intel
  (900) failed all 12 of their calls each, yet $0.01 per call settled on-chain
  into Telegraph escrow credit (not billed). A buyer who pays per call pays
  even when the provider serves nothing — that is the commercial problem
  TrapTest's verified ranking exists to expose.
- **Buyer/user:** Telegraph itself, and every agent/builder choosing an
  `ONCHAIN_TX_LOOKUP_GENERAL` provider — they need verified ranking trust
  before spending on intelligence. The ranking is the product; a
  ranking nobody can audit has no buyer.
- **Intended payer and route to revenue (a case, not a result):**
  no buyer has paid or committed. The intended path is free public
  leaderboard → paid continuous verification: a provider or buyer pays
  for ongoing trap runs, alerts when a provider's answers degrade, and
  a verified-ranking badge backed by receipts. A provider paying to be
  ranked is not assumed — the paying customer is the buyer who needs
  the ranking to be trustworthy, and Telegraph itself as the marketplace
  operator whose ranking credibility is at stake. Until a payer is
  evidenced, this paragraph is a proposal, and the submission must say so.
- **Frequency:** per trap run; the live leaderboard is re-run over the
  fixed trap set, and a reviewer can re-run it with a new trap input.
  Continuous (e.g. daily) re-runs are the paid-tier shape, not a
  claimed current cadence.
- **Demo flow:** one trap input → competing answers bought on testnet →
  pass/fail with receipts → leaderboard re-ranks (see
  `docs/how-to-run.md` §3 and `docs/demo-script.md`).
- **Observed cost:** Billed $0.26 total including $0.02 smoke tests ($0.24
  in the run file + $0.02 smoke), at $0.01 per served call from the live 402
  challenges. A further $0.24 settled on-chain into Telegraph escrow credit,
  NOT billed (Sigil $0.12 + OnChain Intel $0.12 — failed calls that still
  settled; see `docs/how-to-run.md` §4). Burner wallet 30.00 → 29.50 test
  USDC (drop $0.50, verified on-chain 6 Nov 2026). The confirmed free
  allocation was 30 self-minted test USDC + PoW-faucet Sepolia gas; billed
  spend is inside the $0.50 session cap.
- **Observed result (corrected re-score, 8 Nov 2026; strict original Truvian
  3/12, field accuracy 36/47):** 5 providers scored over 12 frozen traps.
  Truvian 8453: 4/12 (t07 + t08 reverted, t11 + t12 unknown-tx; field
  accuracy 37/47 — t08 newly passes under the fixed normaliser, its
  `value_eth` 1e-05 equalling the expected 10000000000000 wei). TxLens 9002:
  2/12 (t11 + t12 only — it answered `not_found` for all 10 mined txs;
  field accuracy 2/47). LiveCert 4433: 0/12 served (503 `no_compatible_miner`
  on all 12). Sigil 9010: 0/12 served (HTTP 500 upstream 404). OnChain Intel
  900: 0/12 served (HTTP 500 upstream 400, "Could not determine a supported
  chain"). The three unserved providers are an UNSERVABLE tier, not a 0%
  pass rate. Truvian's 6 other fails are a schema gap, not wrong answers:
  on t01, t02, t05, t06, t09, t10 its block/from/to/value were all
  correct and only `status` was missing (null for confirmed txs) —
  scored FAIL under the strict rules and reported as such. No provider
  failed by inventing data for an unknown tx: TxLens and Truvian both
  answered `not_found` correctly on t11/t12 and passed those traps.
  **Small-margin caveat:** Truvian 4/12 vs TxLens 2/12 differ by two traps
  on n=12 — treat that as evidence, not a proven gap; one trap either way
  would halve or erase the margin. The token traps t03/t04 score 0 passes
  for every provider even with value excluded (status/from/to/block only),
  so the value-excluded view changes no pass count.
- **Honest limits (repeat on the submission surface):** [No independent
  adoption is claimed. All usage to date is testnet evaluation by the
  author during the event window. Testnet use is not adoption. No user,
  retention, accuracy, or time-saved figure is claimed.]
- **Mainnet readiness:** TrapTest uses the same Direct Ask flow on mainnet as
  on testnet — the Engine and contract addresses are parameters, not
  hardcoded testnet values, and there are no testnet-only shortcuts in the
  scoring path (the same strict scorer, frozen trap discipline, and
  receipt verification apply). Moving to mainnet changes only the funding
  (real USDC instead of self-minted test USDC) and the trap set (mainnet
  transactions with ground truth checked against public chain data); no code
  change to the buy–score–rank loop is needed. No mainnet run has been made
  and none is claimed.
- **How to try:** repo https://github.com/OlsOls4/traptest (live-build
  files to be pushed before submission — see truth list). Reviewer
  replay: `python3 scripts/full_run.py` and
  `python3 scripts/mini_run.py` (frozen trap set, own burner funded as
  in `docs/how-to-run.md` §1); or inspect the evidence without spending
  — `docs/leaderboard/` renders the corrected `results.json`, and every
  served row carries its `cost_usd`, `signal_hash`, and Telegraph
  receipt.

## 4. Submission contents checklist (H2 website)

- [ ] Project details (TrapTest, Evaluator-led; submit evaluation material at
  anjoman.ai/dashboard/eval — verified route, 8 Nov Discord findings: no
  sign-in on the hackathon website, sign in on anjoman.ai; no GitHub bounty
  issue exists for this intent, so nothing to /claim; final submission form
  opens later and will be shared in Discord before 1 Dec)
  — **VERIFIED 8 Nov; watch Discord for the final form opening.**
- [x] Demo video, 2–5 min: hook → one live judge path (input → competing
  answers → pass/fail with receipts → re-rank) → failure case on screen
  → how to reproduce. No mock footage presented as live. **DONE 6 Nov:
  v1, 2:36, local file `docs/demo-video/traptest-demo-2026-11-06.mp4` —
  superseded by v2 (2026-11-08), `docs/demo-video/traptest-demo-2026-11-08.mp4`,
  DONE 8 Nov 2026 — v2, 2:42.**
- [x] How-to-run (`docs/how-to-run.md`, final version with the live
  command filled in) — **DONE 6 Nov.**
- [x] Evidence: live `results.json` + receipts/requests/accounting
  (cost per call, signal hashes, Telegraph receipts) — event-period only.
  **DONE 6 Nov: 60 rows, 24 receipts verified on-chain, escrow accounting
  included. Corrected re-score 8 Nov: Truvian 4/12 (strict 3/12), TxLens
  2/12 — see `results-live/results-corrected-2026-11-08.json`.**
- [x] Short public summary (§2, frozen wording) — **DONE (unchanged
  from draft; it was already accurate).**
- [x] Showcase permission + commercial summary (§3) — **DONE 6 Nov,
  real numbers only.**
- [ ] Disclosure: prep scaffold reused (own code, written before 1 Nov);
  major open-source reuse, if any, disclosed with licences — **to
  confirm at submission (no third-party code beyond stdlib + the
  Telegraph Engine API; state that).**

## 5. Submission-check steps (hackathon_submission_check skill)

1. **Freeze the truth list** (§1) before the final polish round; derive
   each entry from its own source.
2. **Sweep every surface** — repo docs, leaderboard page, video script,
   submission description, README — for every superseded version label,
   test count, cost figure, and provider name. Update each hit to the
   truth list or remove the stale file. In particular: no mock provider
   id, mock hash, mock pass rate, or mock cost may survive on any
   submitted surface; the red MOCK banner must be gone from the live
   page only because it is fed by live data, not because it was deleted
   while still showing mock data.
3. **Verify the live page** in the live browser: submission status,
   video, description lines, and evidence links against the truth list.
   Treat a cached text fetch as unproven if it contradicts a live
   check — reopen the live page to settle it.
4. **Batch the final save:** one description save, one artifact/repo
   update, one verification of the live result. Apply a late change
   only if it fixes a dangerous contradiction.
5. **Stop risky saves with time buffer** before 1 Dec 23:59 UTC — do
   not swap artifacts or repaste descriptions in the final minutes.
6. **Report the verified live state** after the final save (status,
   video version/length, evidence links) so the next check starts from
   a confirmed state.

## 6. Gaps for the live demo (6 Nov 2026 status)

- [ ] Day-1 gates: prize-payment terms (UK) — **STILL UNPUBLISHED, state
  plainly**; free testnet USDC/gas — **RESOLVED (open mint + PoW
  faucet)**; competing supply re-confirmed live — **DONE (24 miners,
  5 attempted, 2 served)**; Evaluator submission route —
  **VERIFIED 8 Nov (Discord): no sign-in on the hackathon website, sign in
  on anjoman.ai, eval material at anjoman.ai/dashboard/eval, no GitHub
  bounty issue for this intent so nothing to /claim; final submission form
  opens later — watch Discord before 1 Dec**.
- [x] Live purchase loop implemented and run against testnet in-window
  (6 Nov 2026).
- [x] Fixed trap set committed before scoring, ground truth checked
  against public chain data (frozen 13:59:42 UTC, 6 Nov).
- [x] Live `results.json` with real receipts, replacing the mock file —
  and the mock file removed from every submitted surface.
- [x] Demo video recorded from the live run (v1, 2:36), with the failure
  case visible on screen — v2 (2026-11-08) DONE, supersedes v1.
- [ ] Repo public (or as the submission requires) with the final
  how-to-run — **OPEN: live-build files not yet pushed; push state to
  confirm at submission** — and the submission verified live after saving.
