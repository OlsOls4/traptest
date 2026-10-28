# TrapTest — submission pack (skeleton, prep only)

**Status at writing (27 Oct 2026, pre-opening): REGISTERED, not submitted.
No event evidence exists yet. Every [BRACKET] below is a gap to be filled
only with event-period (1 Nov–1 Dec 2026) evidence. Do not fill a bracket
with a mock, estimated, or pre-window number.**

## 1. Truth list (freeze before the final polish round)

Derived from its own source, not copied from another document. Any number
not on this list is unverified and must not appear on a submission surface.

| Item | Value | Source |
|---|---|---|
| Hackathon / window / deadline | Telegraph Season II, 1 Nov–1 Dec 2026, deadline 1 Dec 23:59 UTC | hackathon.telegraphprotocol.com (rules/timeline, read 27 Oct) |
| First integration milestone | 14 Nov 2026 (progress check only, not disqualification) | Same |
| Registration | COMPLETED 27 Oct 2026: Olly McBride, Individual, Discord ols0817, project TrapTest (Python), email ollymcbride4@gmail.com verified; confirmation "You're registered", no reference number shown | Live browser registration, 27 Oct |
| Primary intent | `ONCHAIN_TX_LOOKUP` | Engine catalogue, 27 Oct check |
| Provider supply at check | 23 miners listed, ≥10 usable after filtering list-only endpoints | Engine `/intents/ONCHAIN_TX_LOOKUP/miners`, 27 Oct — **re-fetch at run time; miner ids are not stable** |
| Provider supply re-check | 23 listed, 12 usable-looking by catalogue description (10 Blockscout list-only excluded; VulnFeed excluded as contract-security, not tx-hash lookup) — catalogue presence only, NOT a live probe | Same endpoint, 28 Oct — see `docs/supply-recheck-2026-10-28.md`. Re-fetch again at run time; pre-flight ≥2–3 providers before freezing the trap set |
| Purchase flow | Direct Ask `POST /engine/v1/ask/{minerId}`; price from live 402 challenge, never catalogue `cost_per_call: "0.00"` | docs.telegraphprotocol.com |
| Evidence per served call | `cost_usd`, `signal_hash`, `X-TELEGRAPH-RECEIPT` | Same |
| Testnet | Base Sepolia (chain 84532); USDC `0x036CbD53842c5426634e7929541eC2318f3dCF7e`; Diamond `0x5a2324aA18613FAD4e44bDF0d6c73Ec1f6D87ff8`; Engine `https://devnode.telegraphprotocol.com/engine` | Docs, 27 Oct |
| Judging | /100: Technical 35 (min 24), Commercial 30, Adoption 15, Integration 10, Proof 10; need 70+ | Official rules |
| Prize context | $10,000 programme total; main $7,000 (Apps & Agents $3,000, Miners $2,000, Evaluators $2,000) + $3,000 December challenges. TrapTest is Evaluator-led — do not claim the $10,000 or the $3,000 Apps slice as its prize | Official rules |
| Entry fee | Site says "free to register" (27 Oct) | Live browser |
| Test count | [FILL at submission: `python3 -m unittest discover -s tests` count] | Repo tests |
| Live results | [FILL from event window only: trap-set size, providers scored, total testnet cost, pass rates — each with its receipts file] | Event-period run |
| Demo video | [FILL: version, length (must be 2–5 min), link] | Submission |
| Repo | [FILL: link, public/private state at submission] | GitHub |
| **UNVERIFIED — do not claim** | UK prize eligibility; payout currency/method/timing; free testnet USDC/gas acquisition (no Telegraph faucet documented) | Re-check on/after 1 Nov |

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

- **Buyer/user:** Telegraph itself, and every agent/builder choosing an
  `ONCHAIN_TX_LOOKUP` provider — they need verified ranking trust
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
- **Observed cost:** [FILL: total testnet USDC spent, per-call cost from
  the live 402 challenges, and the confirmed free testnet allocation it
  sat inside. Until filled: ~$0.01/call per docs is an estimate, not a
  measured bill. Also [FILL: cost-accounting total from the run log —
  the commercial summary must not quote a cost that the run log does
  not support.]
- **Observed result:** [FILL: providers scored, pass rates, and at least
  one failing row with its mismatching field — or an honest note that
  no provider failed. Provider answers that could not be mapped to the
  scorer's fields are reported as "unmapped schema, not scored as a
  lie", never as failures.]
- **Honest limits (repeat on the submission surface):** [No independent
  adoption is claimed. All usage to date is testnet evaluation by the
  author during the event window. Testnet use is not adoption. No user,
  retention, accuracy, or time-saved figure is claimed.]
- **How to try:** [FILL: repo link + the exact commands in
  `docs/how-to-run.md` once the live loop exists.]

## 4. Submission contents checklist (H2 website)

- [ ] Project details (TrapTest, Evaluator-led; track choice confirmed
  against the Evaluator-specific submission wording in the live browser)
- [ ] Demo video, 2–5 min: hook → one live judge path (input → competing
  answers → pass/fail with receipts → re-rank) → failure case on screen
  → how to reproduce. No mock footage presented as live; any mock shot
  labelled MOCK on screen.
- [ ] How-to-run (`docs/how-to-run.md`, final version with the live
  command filled in)
- [ ] Evidence: live `results.json` + receipts/requests/accounting
  (cost per call, signal hashes, Telegraph receipts) — event-period only
- [ ] Short public summary (§2, frozen wording)
- [ ] Showcase permission + commercial summary (§3)
- [ ] Disclosure: prep scaffold reused (own code, written before 1 Nov);
  major open-source reuse, if any, disclosed with licences

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

## 6. Gaps for the live demo (to be filled only with event-period evidence)

- [ ] Day-1 gates passed: prize-payment terms (UK), free testnet
  USDC/gas (burner wallet + balance at the USDC contract), competing
  supply re-confirmed live, Evaluator submission wording confirmed.
- [ ] Live purchase loop implemented (`ProviderClient.buy` is currently
  `NotImplementedError` by design) and run against testnet in-window.
- [ ] Fixed trap set committed before scoring, ground truth checked
  against public chain data.
- [ ] Live `results.json` with real receipts, replacing the mock file —
  and the mock file removed from every submitted surface.
- [ ] Demo video recorded from the live run (2–5 min), with the failure
  case visible on screen.
- [ ] Repo public (or as the submission requires) with the final
  how-to-run, and the submission verified live after saving.
