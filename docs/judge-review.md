# TrapTest — Independent Judge Review (prep only, 27 Oct 2026)

> **CORRECTION — 9 Nov 2026: the rubric in this file is SUPERSEDED.**
> This review (27 Oct) scored against the then-assumed rubric — Technical 35
> (min 24/35), Commercial 30, Adoption 15, Integration 10, Proof 10 — which
> was never the Evaluator rubric. The **correct rubric is the Evaluator
> TRACK 03 rubric, verified live 8 Nov 2026** from the rules page: **/100,
> need 70+ AND pass 28/40 on Measurement validity** — Measurement validity
> **40 (minimum 28/40)**, Integrity **15**, Reproducibility **10**,
> Coverage/improvement **10**, Documentation **5**, Organic growth **20**
> (5+5+5+5). Every score table in this file (§1, §6-Nov addendum, §8-Nov
> addendum) was computed under the OLD rubric and is preserved below as
> history, labelled as such — **none of it is a score under the correct
> rubric and none of it is comparable to one**. Where this file states the
> old rubric as "official criteria", that claim is wrong and is annotated
> in place. The substance that survives the rubric change — the risk
> register (§2), the adoption-ceiling honesty rule (§4, now mapping to
> Organic growth /20 rather than Adoption /15), and the live-evidence
> record — is kept intact. Evaluator pool: $2,000 = 4×$300 delivery +
> $500/$300 excellence; direct /dashboard/eval submission confirmed
> eligible for the delivery awards (Ahmed Ali, 8 Nov 2026).

**Role:** strict Telegraph Season II judge, scoring against the official criteria
**[as understood 27 Oct 2026 — see the 9 Nov correction banner: this was the
assumed rubric, not the verified Evaluator TRACK 03 rubric]**.
**Scope reviewed:** `~/workspace/hackathon-ideation/telegraph/IDEATION.md` (full),
`~/workspace/telegraph-traptest/README.md`, and `traptest/*.py`
(`traps.py`, `scoring.py`, `leaderboard.py`, `providers.py`) plus
`tests/test_scoring.py`.
**What was NOT done:** no live calls, no purchase/wallet code, no results invented.
The 5 prep unit tests were re-run locally (mock fixtures only) and pass.
**Status at review time:** registered 27 Oct 2026 (Olly McBride, Individual,
Discord ols0817, project TrapTest). Prep only until the 1 Nov window opens.
No live evidence exists yet — and this review scores that fact, not the idea's promise.

**Headline verdict: as it stands today this entry FAILS both gates.
It is a good framework for a potentially passing entry, not a passing entry.**
The idea is genuinely strong; the current artefact is not yet a submission.

---

## 1. Scored assessment of the current prep

**[SUPERSEDED RUBRIC — see correction banner at top. The criteria below
were the assumed rubric on 27 Oct 2026, not the verified Evaluator TRACK 03
rubric. This section is history, not a current score.]**
Assumed criteria at the time: /100, need 70+, with Technical 35 (minimum 24/35),
Commercial 30, Real independent adoption/retention 15, Telegraph
integration quality 10, Proof/demo/tutorial/repeatability 10.

### As-is score (prep framework only, 27 Oct 2026, OLD rubric)

| Criterion | Score | Why — credit given and credit withheld |
|---|---|---|
| Technical quality & mainnet readiness (/35) | **13** | Credit: clean, small, readable code; strict deterministic scoring (status mismatch fails outright, missing field is a failure, never a pass); sensible ranking (pass rate, then traps run, then lower cost; zero-trap providers unranked); trap schema enforces a valid tx hash and a closed status vocabulary; live purchases are correctly *refused* in prep (`NotImplementedError`), which protects the event-period evidence rule. Withheld: there is no live loop at all — no purchase, no runner/CLI, no trap set (only a schema), no answer normalisation, no receipt *verification* (receipt presence is a boolean passed in, never checked against `X-TELEGRAPH-RECEIPT` or `signal_hash`), no error/timeout/402 handling, no mainnet-readiness argument (parameterised endpoints, same flow on mainnet), and no reviewer-replayable run. A framework is not a working product. |
| Commercial viability (/30) | **8** | Credit: the buyer is identified and plausible — Telegraph itself and every builder choosing a provider benefits from verified ranking trust — and the one-line ambition claim is real (no Season I winner policed the ranking). Withheld: no payer, no price, no frequency, no willingness-to-pay evidence, no commercial summary (user/buyer, frequency, demo flow, observed cost, result, how to try), no route from a free leaderboard to revenue, and no answer to "why would a provider pay to be ranked, or a buyer pay for a ranking they can read free?" |
| Real independent adoption / retention (/15) | **0** | Nothing to score. There are no users, no repeat users, no external buyers, and no retention signal. This is honest, not a penalty for dishonesty — but it is a zero, and see §4 for the ceiling even after a perfect build. |
| Telegraph integration quality (/10) | **2** | Credit: the intended integration is the right one — Direct Ask (`POST /engine/v1/ask/{minerId}`) per competitor, price from the live 402 challenge, evidence fields (`cost_usd`, `signal_hash`, receipt) named correctly, and miner IDs re-fetched at run time rather than hardcoded. Withheld: none of it has been executed. `fetch_intents`/`fetch_miners` exist but are untested against the live Engine response shape (they assume `intents`/`miners`/`data` keys), and no Telegraph request, transaction, or accounting evidence exists. An intended integration scores almost nothing. |
| Proof / demo / tutorial / repeatability (/10) | **2** | Credit: 5 mock unit tests pass and are explicitly labelled mock-only (good discipline — they are never presented as event evidence), and the README freezes a truth list. Withheld: no demo video, no how-to-run for a live loop, no receipts, no reviewer input path, no failure case demonstrated, no trap set a reviewer could re-run. |
| **Total** | **25 / 100** | **FAILS 70+ overall and FAILS the 24/35 technical minimum (13/35). [OLD rubric — historical.]** |

### Technical-minimum risk, stated honestly

**As-is, the technical minimum is not close — it is failed by 11 points.**
That is not a borderline judgement call; it is structural. The 13 points are
for design and discipline. The missing 11+ points can only come from a
working, reviewer-replayable live loop: real Direct Ask purchases from ≥2
competing providers, scored against a frozen trap set, with verified receipts
and a run a reviewer can repeat with a new input. Until that loop exists,
no amount of polish to the scoring module moves the technical score over 24.

### Projected score IF the planned build completes fully (OLD rubric — historical projection only, not under the correct Evaluator rubric)

This is a projection, not a score — it assumes the day-1 gates pass, the
live loop works, the demo and receipts are complete, and the reviewer can replay it:

| Criterion | Projected range | Binding constraint |
|---|---|---|
| Technical (/35) | 27–30 | Needs the full loop + receipt verification + mainnet-readiness note; a leaderboard UI alone does not add points here. |
| Commercial (/30) | 18–22 | Needs a written commercial summary with a named payer and a credible free-to-paid path; the idea alone caps here. |
| Adoption (/15) | 3–6 | **Structural ceiling — see §4.** Even a perfect build cannot honestly claim independent adoption by 1 Dec. |
| Integration (/10) | 9 | Achievable if purchases are genuinely autonomous, per-provider, and receipted. |
| Proof (/10) | 8–9 | Achievable with a 2–5 min demo, how-to-run, receipts bundle, and a reviewer failure case. |
| **Total** | **65–76, central ~71** | **Borderline [OLD rubric projection — historical].** A completed TrapTest is a plausible pass, not a safe one. It passes only if Technical lands at the top of its range *and* Commercial is argued tightly, because Adoption cannot rescue a shortfall elsewhere. |

Implication for the build: there is no slack. Every item in §2 must be fixed;
dropping any one of them plausibly drops the total below 70.

---

## 2. Top 5 risks that could drop it below 24/35 technical or 70 overall

Each risk states the failure mode, the score damage, and a concrete fix.

### Risk 1 — The free testnet USDC/gas gate fails (binary, blocks everything)

- **Failure mode:** no Telegraph/organiser source documents a faucet or
  acquisition step for Base Sepolia testnet USDC/gas. If no free route works
  on day 1, no Direct Ask purchase can be made at all — no live loop, no
  receipts, no leaderboard, no reviewer replay.
- **Score damage:** Technical collapses toward single figures, Integration
  → 0, Proof → ~2. Total falls to ~20–30 regardless of how good the
  framework is. This is the only risk that kills the entry outright.
- **Concrete fix:** make this the *first* action on 1 Nov, before any
  TrapTest spending code is written: attempt a faucet claim into a burner
  wallet and confirm the balance lands at Telegraph's USDC contract, then
  record the confirmed allocation and cap the trap set inside it
  (see Risk 4 for sizing). If the claim fails, **stop** — do not buy or
  bridge with real money unless Olly explicitly approves that specific
  spend, because the zero-cost bar then fails for the whole entry.
  Do not spend build days on a UI for a loop that may never be fundable.

### Risk 2 — Provider answer schemas do not match the scorer's assumptions

- **Failure mode:** `scoring.py` assumes provider answers arrive as a flat
  dict with keys `status`, `from`, `to`, `value`, `block`, with comparable
  units and vocabulary. Real providers may return nested payloads, different
  field names, free text, values in wei vs ether, hex vs decimal blocks,
  checksummed vs lowercase addresses, or a different status vocabulary.
  Under the current strict scorer, a *correct* provider whose schema is
  unmapped fails every trap — so the leaderboard would present schema gaps
  as lies, which destroys the entry's whole trust claim and invites a
  technical-minimum failure on "accurate claims" grounds.
- **Score damage:** Technical −8 to −12 (a leaderboard that mislabels
  providers is worse than no leaderboard); Proof also falls because the
  reviewer cannot trust the pass/fail display.
- **Concrete fix:** build a normalisation/mapping layer *from observed live
  answers in the event window*, before the scored run: per-provider field
  mapping, case-insensitive address comparison, wei/ether and hex/decimal
  normalisation, and a documented status-vocabulary map. Keep the strict
  rule (a genuinely missing or wrong field is a failure), but add a
  separate, explicitly labelled outcome — "unmapped schema, not scored as
  a lie" — recorded in the run log whenever a provider's payload cannot be
  mapped, and do not rank a provider on unmapped traps. Publish the mapping
  table with the submission so a reviewer can audit it.

### Risk 3 — Competing-provider supply collapses at run time

- **Failure mode:** miner IDs are unstable, providers go offline, or the
  trap intent is served only by list-only endpoints that do not answer a
  tx-hash query. A leaderboard with one provider — or zero — is not a
  leaderboard; it is a single-provider check wearing a leaderboard's name.
  The 27 Oct verification (23 `ONCHAIN_TX_LOOKUP` miners, ≥10 usable) is a
  snapshot, not a guarantee for the event window.
- **Score damage:** Technical −6 to −10 and Integration −4; the core
  "competing providers re-ranked" claim evaporates.
- **Concrete fix:** on day 1, re-fetch the live catalogue and pre-flight
  at least 2 (ideally 3+) tx-capable providers with a cheap probe *before*
  freezing the trap set; freeze only traps those providers actually serve.
  Decide the fallback early, not at the deadline: if fewer than 2 providers
  answer, either extend to a second trap intent with the same
  ground-truth discipline (e.g. `CRYPTO_TRANSFER_VERIFY`, 20 miners at
  27 Oct verification — re-check live) or promote the Sentinel fallback
  while there is still build time. Never present a one-provider table as a
  leaderboard.

### Risk 4 — The trap set is not credible (tuned, too small, or all-trivial)

- **Failure mode:** traps chosen after seeing answers, traps that all pass
  (no discrimination), traps whose ground truth is not independently
  sourced, or a set so small that one trap flips the ranking. With the
  planned "tens of traps × 2 providers", pass-rate differences of one trap
  are noise, and a judge who suspects cherry-picking will discount the
  entire leaderboard.
- **Score damage:** Technical −6 to −10 (the scoring claim is the product);
  Commercial also falls because an untrustworthy ranking has no buyer.
- **Concrete fix:** freeze the trap set *before* the first scored purchase
  and publish the freeze (trap IDs, tx hashes, expected values, ground-truth
  sources, and a timestamp/commit) with the submission. Include a
  discriminating mix: confirmed, reverted, high-value, old-block, and at
  least one `not_found` trap (a hash that does not exist — a provider that
  invents data for it fails loudly, which is exactly the lie-detector
  story). Ground truth must come from public chain data checked at build
  time, never invented. Recommended floor: **≥10 traps × ≥2 providers =
  ≥20 scored calls** (~$0.20 in testnet USDC at the docs' ~$0.01/call
  figure, plus the 2% protocol fee — an estimate to be replaced by observed
  402 prices, and capped inside the confirmed free allocation from Risk 1).

### Risk 5 — Submission-track mismatch and reviewer replay failure

- **Failure mode (two halves, same outcome):** (a) the entry is built and
  framed as Evaluator-led, but the submission route, prize pool, or
  artefact format turns out to be Apps-shaped (see §3) — the entry is then
  judged against requirements it was not built to meet, including the Apps
  requirement of a genuinely autonomous machine-to-machine purchase used
  for a meaningful task; (b) the reviewer cannot replay the loop because
  the demo needs a funded wallet, private keys, local setup, or a hosted UI
  that does not exist, or because receipts are shown as screenshots rather
  than inspectable evidence.
- **Score damage:** either half can cost the technical minimum outright
  (reviewer cannot run it with a new input, check the result, inspect the
  real request/transaction evidence, or test a failure case) and Proof
  falls to ~2–3. Combined damage: −15 to −20 overall.
- **Concrete fix:** confirm the Evaluator submission wording in the live
  browser *before* building the final pack (see §3 checklist), and design
  the submission to satisfy the documented Apps bar as well where
  possible: an autonomous loop that buys, scores, and publishes (not a
  manual script run), plus a one-command reviewer replay with a new trap
  input, a built-in failure case (a stale/wrong answer shown failing),
  an inspectable receipts bundle (request, `cost_usd`, `signal_hash`,
  `X-TELEGRAPH-RECEIPT` per call), and a how-to-run that does not require
  the reviewer to fund a wallet (pre-run evidence is the default; optional
  replay with the reviewer's own testnet funds is documented separately).
  Add a one-paragraph mainnet-readiness note: same Direct Ask flow,
  parameterised Engine/contract addresses, no testnet-only shortcuts.

**Also noted, below the top 5:** `providers.py` catalogue fetching is
untested (no test covers `fetch_intents`/`fetch_miners`, and their response
shape assumptions are unverified against the live Engine); the leaderboard
tracks cost but nothing verifies `cost_usd` against the live 402 challenge;
there is no cost-accounting total for the commercial summary; and there is
no CLI/runner, demo, or how-to-run yet. These are build tasks, not separate
score risks, provided Risks 1–5 are handled.

---

## 3. Is the Evaluator-led framing defensible? (Missions are Apps-only)

**Short answer: defensible in spirit, unproven as a submission route —
and it must be confirmed before the final pack is built, not at submission time.**

What supports it:

- Season I had a distinct Evaluators/Script Authors track ($1,000 of the
  $5,000 Season I pool), won by script authors — scoring providers per
  Intent is recognisably Evaluator work, and TrapTest *is* that work:
  fixed inputs, deterministic scoring, a published ranking.
- The frozen rules as read state that Miners/Evaluators pick Intents while
  Apps & Agents pick missions, and that one registration covers all three
  tracks with the submission choice made later. Nothing in the registration
  locked TrapTest to a track, so reframing at submission is still open.
- The registration itself was submitted with the project described as an
  evaluator, which is consistent, not contradictory.

What undermines it, and why it cannot be assumed:

- The task brief for this review states missions are Apps-only, and the
  frozen rules' *detailed* entry requirements (autonomous M2M purchase,
  meaningful use of the intelligence, reviewer replay, demo, commercial
  summary) are written in Apps & Agents terms. The Evaluator-specific
  submission wording (§5/§8 in the source notes) was **unverified** — a
  text fetch defaulted to the Apps view. If Season II Evaluator submissions
  are script-based (a scoring script submitted through a different route,
  judged as a script, with a $2,000 Evaluators pool rather than the $3,000
  Apps & Agents pool), then a website project submission with a leaderboard
  UI may be judged as an App anyway — or may not fit either route cleanly.
- The prize consequence matters: Evaluator pool **$2,000 = 4×$300 delivery +
  $500/$300 excellence** (verified 8 Nov 2026). **[CORRECTED 9 Nov 2026:
  the original text here quoted "Evaluators $2,000 vs Apps & Agents $3,000
  (of the $7,000 main pool)" — the Apps-pool figure and the $7,000 total
  were from the unverified pre-8-Nov reading and are not the Evaluator terms
  that apply to this entry. The Evaluator $2,000 figure itself stands.]**
  Direct /dashboard/eval submission was confirmed eligible for the delivery
  awards by Ahmed Ali (8 Nov 2026), so the delivery-award lane is open to
  this entry; a single entry cannot be submitted to both tracks — the
  rules allow multiple tracks only as separate, distinct entries.
- TrapTest's strongest defence against this risk is that its core loop
  already satisfies the Apps bar: it makes genuinely autonomous
  machine-to-machine purchases (Direct Ask buys from competing providers)
  and uses the intelligence for a meaningful task (scoring and publishing
  a ranking that buyers use to choose providers). It does not *need* the
  Evaluator label to be legitimate; the label is a framing choice, not the
  substance.

**Confirm before submitting (live browser, Evaluator track selected):**

> **[RESOLVED 8 Nov 2026 — see bracketed answers. Kept as history; the
> checklist below no longer blocks submission.]**

1. Does Season II accept Evaluator entries through the H2 website
   submission flow, or through a separate script-submission route?
   **[RESOLVED 8 Nov: no sign-in on the hackathon website and none needed;
   sign in on anjoman.ai and submit material at
   anjoman.ai/dashboard/eval. No GitHub bounty issue exists for
   ONCHAIN_TX_LOOKUP_GENERAL, so there is nothing to /claim.]**
2. What artefact does an Evaluator entry submit — a scoring script, a
   report, a live leaderboard, or all three — and is a UI leaderboard
   counted as Evaluator work or as an App?
   **[RESOLVED 8 Nov: evaluation material (preference pairs + truth
   source) submitted directly at /dashboard/eval; 12 pairs + 1 truth
   source ADMITTED 8 Nov 11:20–11:21.]**
3. Does an Evaluator entry need to show an autonomous purchase, or is
   scoring answers purchased by the evaluator sufficient?
   **[RESOLVED 8 Nov: direct /dashboard/eval submission qualifies for the
   4×$300 delivery awards (Ahmed Ali, 8 Nov 13:36).]**
4. Which prize pool applies to a TrapTest-shaped entry, and can one entry
   win a delivery award in one track only?
   **[RESOLVED 8 Nov: Evaluator pool $2,000 = 4×$300 delivery + $500/$300
   excellence; direct submission eligible for delivery awards.]**
5. Is there any Evaluator-specific field or format (e.g. Intent selection,
   script link) that the Apps submission form does not have?
   **[OPEN: the final submission form does not exist yet — it opens later
   and will be shared in Discord before the 1 Dec deadline.]**

**Recommendation:** confirm items 1–5 first. **[UPDATE 9 Nov 2026: items
1–4 are confirmed/resolved as annotated above (8 Nov); only item 5 — the
final submission form — remains open, because the form does not exist yet.]**
If the Evaluator route is
confirmed and fits a leaderboard-plus-script artefact, submit as Evaluator
(the framing is then honest and the work matches the track). If it is
unclear or script-only, submit as Apps & Agents — the loop satisfies the
Apps purchase requirement, the prize pool is larger, and the documented
submission format is known. Do not submit the same artefact to both tracks.

---

## 4. Adoption-ceiling honesty — how the submission must phrase it

**[RUBRIC MAPPING — 9 Nov 2026: this section was written against Adoption
/15 in the old rubric. Under the correct Evaluator rubric it maps to
Organic growth /20 (5+5+5+5 — dated public updates, tutorial/education,
evidence an independent developer reproduced the work, developer
activation). The substance is unchanged: no independent adoption can
honestly be claimed, and the "3–6" ceiling below is a ceiling on the
adoption-like credit, not a score under the current rubric.]**

**The ceiling:** no TrapTest submission can honestly claim real independent
adoption or retention by 1 Dec 2026. Testnet use is explicitly not adoption,
and manufactured adoption is a disqualifier. The honest Adoption score for
a completed build is **3–6/15 at most** (credit only for reviewer
repeatability and any genuine external interest that is evidenced, not
asserted). Any submission that claims more will lose credibility with the
judge on every other criterion too — a judge who catches one inflated claim
discounts the rest.

**Forbidden phrasing (do not use, in the submission, demo, or README):**

- "Users", "adopted by X builders/providers", "growing user base",
  "retention", "traction", "demand" — unless each is backed by named,
  independent, verifiable evidence from the event window.
- Counting as adoption: the author's own purchases, the author's own
  leaderboard views, reviewer replay runs, Discord/Telegram interest or
  messages, stars/forks, or a provider "agreeing" the ranking is useful.
- Counting a self-purchase (including from a second wallet) as an external
  sale or as adoption — this is manufactured adoption and a disqualifier.
- "Testnet users" presented as users without the testnet qualifier, or any
  sentence where testnet activity is left to imply production use.

**Required phrasing (use verbatim in substance, in the submission's
adoption/commercial sections):**

> "No independent adoption is claimed. All usage to date is testnet
> evaluation by the author during the event window (1 Nov–1 Dec 2026).
> Testnet use is not adoption. The leaderboard has not been adopted by
> independent builders or providers, and no retention is claimed."

**What may honestly be claimed instead (with evidence, not assertion):**

- Reviewer repeatability: "A reviewer can re-run the fixed trap set and
  reproduce the pass/fail table; receipts for each call are included."
- Observed provider behaviour, if and only if it is evidenced: e.g.
  "Provider X returned a stale answer on trap T on [date]; on re-run
  after [date] it returned the correct answer" — with both receipts
  attached. That is an observation, not a retention claim.
- Genuine external interest, strictly labelled: "Unprompted enquiries
  received: [count], [source], [date]" — only if they exist and are
  verifiable, and never upgraded into "users" or "demand".
- The forward commercial case, labelled as a case, not a result: "The
  intended buyers are Telegraph and builders choosing a provider; no
  buyer has yet paid or committed."

**Scoring consequence to accept:** budget Adoption at 3–6/15 in every
projection **[OLD rubric; under the correct rubric this is the adoption-like
share of Organic growth /20, which is likewise capped near the bottom by the
same honesty rule — no independent adoption, no retention, no public
reproduction evidenced yet]**. The entry passes, if it passes, on Technical + Commercial +
Integration + Proof — which is why §2's fixes are non-negotiable. Do not
try to close the Adoption gap with wording; a judge rewards the honesty
and penalises the inflation.

---

## Addendum — live build review (6 Nov 2026)

**Scope reviewed:** the 6 Nov 2026 live run — `traps-frozen-2026-11-06.json`
(12 traps, frozen 13:59:42 UTC, before the first scored purchase),
`results-live/full-run-2026-11-06.json` (60 rows, `data_kind: LIVE`),
`scripts/full_run.py` + `scripts/mini_run.py`, `docs/leaderboard/`
(rendered and screenshotted live), `docs/demo-video/` (2:36 video),
42/42 unit tests green. The prep review above (§1–§4) is preserved as
history; this addendum re-scores on the live evidence only.

### Results (all event-period, receipts on-chain)

| Provider | Served | Passed | Cost billed | Note |
|---|---|---|---|---|
| Truvian 8453 | 12/12 | **3/12** | $0.12 | Passed t07 (reverted), t11 + t12 (unknown-tx). |
| TxLens 9002 | 12/12 | **2/12** | $0.12 | Passed t11 + t12 only; answered `not_found` for all 10 mined txs. |
| LiveCert 4433 | 0/12 | 0/12 | $0 | 503 `no_compatible_miner` on all 12. |
| Sigil 9010 | 0/12 | 0/12 | $0 (+$0.12 escrow) | HTTP 500 upstream 404 on all 12. |
| OnChain Intel 900 | 0/12 | 0/12 | $0 (+$0.12 escrow) | HTTP 500 upstream 400 "Could not determine a supported chain" (upstream still on old `ONCHAIN_TX_LOOKUP` intent). |

Session accounting (verified on-chain): billed $0.26 (smoke $0.02 +
full run $0.12 + Truvian $0.12); $0.24 settled into Telegraph escrow
credit, not billed; burner wallet 30.00 → 29.50 test USDC. Billed spend
is inside the $0.50 session cap; out-of-wallet total including escrow
credit is exactly $0.50. All 24 served receipts verified on-chain
(`receipt_verified_onchain: true`).

### Risk register — updated

- **Risk 1 (funding) — RESOLVED, with a finding.** No Telegraph faucet
  exists, but the accepted token has an open mint and burner 3
  self-minted 30 test USDC (other builders do the same); gas from the
  PoW faucet. Zero real money. The funding route is documented, not
  assumed.
- **Risk 2 (schema mismatch) — PARTLY REALISED, handled honestly.**
  Truvian returns no `status` for confirmed transactions: on t01, t02,
  t05, t06, t09, t10 every returned field was correct and the ONLY
  failing field was `status`. Under the strict scorer these are FAILs
  (a missing field is a failure), and the pack reports them as a schema
  gap, not as lies — exactly the outcome the prep review prescribed.
  TxLens's `not_found` answers are wrong answers, not a schema gap.
  Normalisation (block_number → block, value_eth → value, ETH→wei) is
  implemented in the run harness and recorded per row; raw answers are
  kept alongside normalised ones.
- **Risk 3 (supply) — PARTLY REALISED.** 24 miners listed, but only 2
  of 5 attempted providers served the intent. The leaderboard is still
  a real comparison (2 serving providers, 3 documented unservable) —
  but the "competing providers" claim now rests on 2, not 5, and the
  unservable three are evidence of network immaturity, not of TrapTest
  failing to look. No second intent was added; the task brief forbade
  tuning traps and the frozen set was never touched.
- **Risk 4 (trap credibility) — HELD.** Set frozen before the first
  scored purchase (13:59:42 UTC), 12 traps, 2/category, ground truth
  from public Base Sepolia RPC with per-trap provenance. No trap was
  changed after seeing answers. Small-sample caveat stands: a 1-trap
  difference (3 vs 2) is noise, and the pack must say so — the ranking
  is evidence, not a verdict on provider quality.
- **Risk 5 (track mismatch / replay) — HALF OPEN.** The loop is real,
  autonomous, receipted, and replayable (`scripts/full_run.py`,
  `scripts/mini_run.py`, `docs/how-to-run.md`). The Evaluator-route
  confirmation (§3 checklist) is STILL NOT DONE — it needs a live
  browser check with the Evaluator track selected, which is a human
  step outside this build. If it fails, the Apps & Agents fallback from
  §3 still applies.

### Re-score on live evidence (projection, same OLD criteria — historical only, not under the correct Evaluator rubric)

| Criterion | Prep | Live | Why |
|---|---|---|---|
| Technical (/35) | 13 | **27–29** | Live loop works, frozen set, verified receipts, replayable, normalisation + escrow accounting. Docked: only 2 serving providers; no mainnet-readiness note yet. |
| Commercial (/30) | 8 | **18–20** | Commercial summary now has a named buyer, observed cost, and observed result (see submission-pack §3). Still a case, not a result — no payer evidenced. |
| Adoption (/15) | 0 | **3** | No independent adoption claimed (honest ceiling); credit only for reviewer repeatability. |
| Integration (/10) | 2 | **9** | Real autonomous Direct Ask purchases, per-provider, receipted, fresh catalogue. Docked 1: 3 of 5 providers unservable for the intent. |
| Proof (/10) | 2 | **8–9** | 2:36 demo with visible fails, how-to-run with the live command, receipts bundle, reviewer failure case on screen. |
| **Total** | **25** | **65–70, central ~68** | **Still borderline — likely just under 70.** The live build moved Technical and Proof most of the way, but Adoption cannot rise and Commercial is capped without a payer. The entry is submittable and honest; it is not a safe pass. |

### What would still move the score before 1 Dec

1. **Evaluator-route confirmation** (live browser) — removes the
   track-mismatch risk; without it the submission may be judged as an
   App anyway.
2. **A second serving provider** — a re-run of the mini-run closer to
   submission (catalogue churn is real: 21 miners on 1 Nov, 24 on
   6 Nov) could add a third serving provider and strengthen the
   comparison. Costs $0.12 billed per attempt; cap discipline applies.
3. **Mainnet-readiness note** — one paragraph (same Direct Ask flow,
   parameterised Engine/contract addresses, no testnet-only shortcuts)
   for +1–2 Technical.
4. **Do NOT chase Adoption** — no claim is available and any
   manufactured claim is a disqualifier (see §4).

---

## Conclusion (prep review, 27 Oct 2026 — preserved)

- **As-is score: 25/100 — fails 70+ and fails the 24/35 technical minimum (13/35). [OLD rubric, 27 Oct 2026 — historical only.]**
- **Projected completed score: 65–76, central ~71 — a borderline pass, with no slack. [OLD rubric, 27 Oct 2026 — historical only.]**
- **Single biggest risk: Risk 1 — free testnet USDC/gas acquisition.**
  It is binary and it gates everything: without funded testnet purchases
  there is no live loop, no receipts, no leaderboard, and no reviewer
  replay, and no framework polish compensates. It must be resolved first
  on 1 Nov, before further build time is spent.
- **Second-order risk to watch:** Risk 2 (schema mismatch) — the most
  likely way a *funded, built* TrapTest still fails, by mislabelling
  correct providers as liars.
- **Decision needed before the final pack:** the §3 Evaluator-confirmation
  checklist (live browser, Evaluator track selected). If the Evaluator
  route does not fit a leaderboard-plus-script artefact, submit as
  Apps & Agents.

## Addendum — Council review, 8 Nov 2026 (all six panels in parallel + fresh-judge re-score)

**Scores.** Prior internal re-score 65–70, central ~68. Council first-pass independent
re-scores: Judge A 65/100, Judge B 59–62 (central ~60). After the improvement round,
fresh independent judge (revised artifacts only): **66/100 (range 64–69) on the frozen
snapshot rubric (T35/C30/A15/I10/P10) — FAIL, narrowly; 61/100 (58–64) on the live
Apps-view weights (T35/C25/A10/I5/P5 + Organic growth 20). [Both rubrics here
are OLD/superseded for this entry — see the 9 Nov correction banner at the
top. The correct Evaluator TRACK 03 rubric was verified live 8 Nov; the
features council re-scored 62–63/100 under it on 9 Nov.]** Breakdown: T29, C19, A2,
I8, P8 frozen. The entry does NOT pass 70 on either rubric on central estimate.
The shortfall is structural (zero independent adoption, zero public distribution,
repo push unconfirmed, video local-only) — not code quality.

**Rubric warning (researchers, live fetch 8 Nov 11:03 UTC).** The live rules page
defaults to the Apps & Agents view: T35 (min 24), C25, A10, I5, P5, + Organic growth /
education / developer activation 20 — NOT the frozen snapshot rubric. **[CORRECTED
9 Nov 2026: the Evaluator-view rubric was VERIFIED live 8 Nov (rules page
TRACK 03): Measurement validity 40 (minimum 28/40), Integrity 15,
Reproducibility 10, Coverage/improvement 10, Documentation 5, Organic growth
20 (5+5+5+5); need 70/100 AND pass 28/40. It is no longer unverified.]** The
20-point growth category (≥3 dated public updates, a tutorial,
evidence an independent developer reproduced the work) has no verified activity behind
it yet. The live weights punish this entry *more* than the frozen rubric.

**Corrected re-score (8 Nov, disclosed re-analysis of the same frozen raw answers).**
Truvian 8453: **4/12** (strict 3/12 — t08 was a harness normalisation bug: value_eth
"1e-05" = 10,000,000,000,000 wei), field accuracy 37/47. TxLens 9002: 2/12, 2/47.
LiveCert 4433 / Sigil 9010 / OnChain Intel 900: 0 served (unservable tier, not ranked).
Ranking order unchanged. Value-excluded t03/t04 view: 0 passes for every provider.
Canonical accounting: billed $0.26 incl. $0.02 smoke; $0.24 escrow credit, not billed;
wallet 30.00 → 29.50.

**Evaluator route — RESOLVED 8 Nov.** No sign-in on the hackathon website; sign in on
anjoman.ai. No GitHub bounty issue exists for ONCHAIN_TX_LOOKUP_GENERAL — nothing to
/claim. Material goes in directly at anjoman.ai/dashboard/eval. **SUBMITTED 8 Nov
11:20–11:21: 12 preference pairs + 1 truth source admitted; pool went 4 → 5
contributors (activation threshold met).** Staged fixes for t04/t06/t10 rejected
answers exist in `anjoman-material/review-fixes-2026-11-08/` — NOT yet applied or
re-submitted. Truth source still UNVALIDATED (Anjoman sandbox validator not run).
Whether direct /dashboard/eval submission without a bounty /claim qualifies for the
4×$300 verified-delivery awards is **[RESOLVED 8 Nov 13:36 — Ahmed Ali
confirmed it DOES qualify for the delivery awards, so TrapTest is eligible
for the full $2,000 Evaluator pool. The "excellence-only" risk in the
original text no longer applies.]**

**What the improvement round changed (verified 8 Nov).** Shared `traptest/normalise.py`
(Decimal) + `traptest/receipts.py` (status AND Transfer-log verification); stale token
map fixed (Sepolia accepted token 0xcc19…); leaderboard rewritten (verdict strip,
field accuracy, unserved reasons, corrected + strict tables, honest replay box);
submission-pack/README/how-to-run updated (verified Anjoman route, mainnet-readiness,
escrow finding headlining commercial); parametrised append-only runner
(`traptest/run.py`, dry-run, --spend-cap $0.30 default, no-overwrite); video v2
(2:42, Shot 4 table fixed, Shot 5 re-cropped, receipt overlay, caveat line);
tests 42 → **91/91 passing**; stale-string sweep 8 Nov (zero "re-cut in progress",
"42 tests", "nothing yet", "PREP ONLY" across README/pack/how-to-run/leaderboard/
anjoman README). Frozen files sha256-verified untouched.

**Remaining open items.** (1) ~~Evaluator-view rubric verification (live browser).~~
**[RESOLVED 8 Nov 2026 — Evaluator TRACK 03 rubric verified live: Validity 40
(min 28/40), Integrity 15, Reproducibility 10, Coverage 10, Docs 5, Organic
growth 20; need 70/100 + pass 28/40.]**
(2) Repo push: live-build files not yet confirmed pushed to github.com/OlsOls4/traptest
(no local .git). (3) Anjoman pair re-submission with fixes + truth-source validation.
(4) Publish/distribute — the highest-upside move (+~8 live / +2–3 frozen): public repo,
uploaded video, bounties-repo star (live rules §5 requires it for every track), 3 dated
public posts. (5) Second live re-run (~$0.12–0.24, 26 miners now live) to test whether
4-vs-2 is stable. (6) Final submission form — does not exist yet; watch Discord.
(7) UK prize-payment terms still unpublished. Full record:
`~/workspace/goals/traptest-telegraph-season-ii-submission/hidden_files/council-2026-11-08.md`.
