# TrapTest — Independent Judge Review (prep only, 27 Oct 2026)

**Role:** strict Telegraph Season II judge, scoring against the official criteria.
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

Official criteria: /100, need 70+, with Technical 35 (minimum 24/35),
Commercial 30, Real independent adoption/retention 15, Telegraph
integration quality 10, Proof/demo/tutorial/repeatability 10.

### As-is score (prep framework only, 27 Oct 2026)

| Criterion | Score | Why — credit given and credit withheld |
|---|---|---|
| Technical quality & mainnet readiness (/35) | **13** | Credit: clean, small, readable code; strict deterministic scoring (status mismatch fails outright, missing field is a failure, never a pass); sensible ranking (pass rate, then traps run, then lower cost; zero-trap providers unranked); trap schema enforces a valid tx hash and a closed status vocabulary; live purchases are correctly *refused* in prep (`NotImplementedError`), which protects the event-period evidence rule. Withheld: there is no live loop at all — no purchase, no runner/CLI, no trap set (only a schema), no answer normalisation, no receipt *verification* (receipt presence is a boolean passed in, never checked against `X-TELEGRAPH-RECEIPT` or `signal_hash`), no error/timeout/402 handling, no mainnet-readiness argument (parameterised endpoints, same flow on mainnet), and no reviewer-replayable run. A framework is not a working product. |
| Commercial viability (/30) | **8** | Credit: the buyer is identified and plausible — Telegraph itself and every builder choosing a provider benefits from verified ranking trust — and the one-line ambition claim is real (no Season I winner policed the ranking). Withheld: no payer, no price, no frequency, no willingness-to-pay evidence, no commercial summary (user/buyer, frequency, demo flow, observed cost, result, how to try), no route from a free leaderboard to revenue, and no answer to "why would a provider pay to be ranked, or a buyer pay for a ranking they can read free?" |
| Real independent adoption / retention (/15) | **0** | Nothing to score. There are no users, no repeat users, no external buyers, and no retention signal. This is honest, not a penalty for dishonesty — but it is a zero, and see §4 for the ceiling even after a perfect build. |
| Telegraph integration quality (/10) | **2** | Credit: the intended integration is the right one — Direct Ask (`POST /engine/v1/ask/{minerId}`) per competitor, price from the live 402 challenge, evidence fields (`cost_usd`, `signal_hash`, receipt) named correctly, and miner IDs re-fetched at run time rather than hardcoded. Withheld: none of it has been executed. `fetch_intents`/`fetch_miners` exist but are untested against the live Engine response shape (they assume `intents`/`miners`/`data` keys), and no Telegraph request, transaction, or accounting evidence exists. An intended integration scores almost nothing. |
| Proof / demo / tutorial / repeatability (/10) | **2** | Credit: 5 mock unit tests pass and are explicitly labelled mock-only (good discipline — they are never presented as event evidence), and the README freezes a truth list. Withheld: no demo video, no how-to-run for a live loop, no receipts, no reviewer input path, no failure case demonstrated, no trap set a reviewer could re-run. |
| **Total** | **25 / 100** | **FAILS 70+ overall and FAILS the 24/35 technical minimum (13/35).** |

### Technical-minimum risk, stated honestly

**As-is, the technical minimum is not close — it is failed by 11 points.**
That is not a borderline judgement call; it is structural. The 13 points are
for design and discipline. The missing 11+ points can only come from a
working, reviewer-replayable live loop: real Direct Ask purchases from ≥2
competing providers, scored against a frozen trap set, with verified receipts
and a run a reviewer can repeat with a new input. Until that loop exists,
no amount of polish to the scoring module moves the technical score over 24.

### Projected score IF the planned build completes fully

This is a projection, not a score — it assumes the day-1 gates pass, the
live loop works, the demo and receipts are complete, and the reviewer can replay it:

| Criterion | Projected range | Binding constraint |
|---|---|---|
| Technical (/35) | 27–30 | Needs the full loop + receipt verification + mainnet-readiness note; a leaderboard UI alone does not add points here. |
| Commercial (/30) | 18–22 | Needs a written commercial summary with a named payer and a credible free-to-paid path; the idea alone caps here. |
| Adoption (/15) | 3–6 | **Structural ceiling — see §4.** Even a perfect build cannot honestly claim independent adoption by 1 Dec. |
| Integration (/10) | 9 | Achievable if purchases are genuinely autonomous, per-provider, and receipted. |
| Proof (/10) | 8–9 | Achievable with a 2–5 min demo, how-to-run, receipts bundle, and a reviewer failure case. |
| **Total** | **65–76, central ~71** | **Borderline.** A completed TrapTest is a plausible pass, not a safe one. It passes only if Technical lands at the top of its range *and* Commercial is argued tightly, because Adoption cannot rescue a shortfall elsewhere. |

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
- The prize consequence matters: Evaluators $2,000 vs Apps & Agents $3,000
  (of the $7,000 main pool). Choosing Evaluator-led caps the prize even if
  it wins, and a single entry cannot be submitted to both tracks — the
  rules allow multiple tracks only as separate, distinct entries.
- TrapTest's strongest defence against this risk is that its core loop
  already satisfies the Apps bar: it makes genuinely autonomous
  machine-to-machine purchases (Direct Ask buys from competing providers)
  and uses the intelligence for a meaningful task (scoring and publishing
  a ranking that buyers use to choose providers). It does not *need* the
  Evaluator label to be legitimate; the label is a framing choice, not the
  substance.

**Confirm before submitting (live browser, Evaluator track selected):**

1. Does Season II accept Evaluator entries through the H2 website
   submission flow, or through a separate script-submission route?
2. What artefact does an Evaluator entry submit — a scoring script, a
   report, a live leaderboard, or all three — and is a UI leaderboard
   counted as Evaluator work or as an App?
3. Does an Evaluator entry need to show an autonomous purchase, or is
   scoring answers purchased by the evaluator sufficient?
4. Which prize pool applies to a TrapTest-shaped entry, and can one entry
   win a delivery award in one track only?
5. Is there any Evaluator-specific field or format (e.g. Intent selection,
   script link) that the Apps submission form does not have?

**Recommendation:** confirm items 1–5 first. If the Evaluator route is
confirmed and fits a leaderboard-plus-script artefact, submit as Evaluator
(the framing is then honest and the work matches the track). If it is
unclear or script-only, submit as Apps & Agents — the loop satisfies the
Apps purchase requirement, the prize pool is larger, and the documented
submission format is known. Do not submit the same artefact to both tracks.

---

## 4. Adoption-ceiling honesty — how the submission must phrase it

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
projection. The entry passes, if it passes, on Technical + Commercial +
Integration + Proof — which is why §2's fixes are non-negotiable. Do not
try to close the Adoption gap with wording; a judge rewards the honesty
and penalises the inflation.

---

## Conclusion

- **As-is score: 25/100 — fails 70+ and fails the 24/35 technical minimum (13/35).**
- **Projected completed score: 65–76, central ~71 — a borderline pass, with no slack.**
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
