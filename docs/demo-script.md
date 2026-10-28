# TrapTest — demo script (prep only, 28 Oct 2026)

**Status: SCRIPT ONLY. No footage exists yet and no result is claimed.
Every shot that needs the live loop is marked `[LIVE FOOTAGE]`.
Footage is recorded only in the event window (1 Nov–1 Dec 2026) from a
real run against testnet. Any mock shot used for editing reference must
be labelled MOCK on screen and must never appear in the submitted video
as if it were live.**

Target length: **~3:30** (must be 2–5 min). One voice, plain narration,
captions on. No music bed over narration. No claim about adoption,
users, accuracy, or money saved — none exists yet.

## 0. The 60-second judge path (the spine of the whole video)

One trap input → competing answers bought on testnet → pass/fail with
receipts → leaderboard re-ranks, with a stale/wrong answer failing on
screen. Everything else in the video is set-up for, or payoff from,
that path. If a viewer watches only the first 60 seconds, they must
have seen: what a trap is, two providers answering the same trap, and
at least one pass and one fail (or, if no provider fails in the live
run, an honest on-screen note saying so — see §3).

## 1. Storyboard and narration

### Shot 1 — Hook (0:00–0:20) — no footage needed

On screen: the TrapTest title and one sentence.

> **Narration:** "Telegraph ranks intelligence providers. But who
> checks whether the ranking itself can be trusted? TrapTest does.
> It buys the same question from competing providers — a question
> whose answer is already known — and shows you who got it right."

### Shot 2 — What a trap is (0:20–0:50) — screen capture of the trap file

`[LIVE FOOTAGE: trap file — trap id, intent ONCHAIN_TX_LOOKUP, tx hash,
expected status, from, to, value, block, and the public-chain source
link for the ground truth. No provider answer visible yet.]`

> **Narration:** "A trap is a transaction query with known ground
> truth. This transaction happened on Base Sepolia testnet. Its
> sender, recipient, value and block are checked against the public
> chain record before any provider is scored — so the truth never
> comes from a provider's own answer."

### Shot 3 — One input, two competing buys (0:50–1:30)

`[LIVE FOOTAGE: the runner buying the trap from two competing providers
via Direct Ask, one miner at a time. Show the two request rows and the
Telegraph receipts as they land: cost_usd, signal_hash, and
X-TELEGRAPH-RECEIPT per call. Do not show any wallet, key, or seed.]`

> **Narration:** "TrapTest buys that trap from two competing
> providers, one at a time, through Telegraph's Direct Ask. Each
> served call comes back with a price from the live 402 challenge, a
> signal hash, and a Telegraph receipt. Those receipts are the
> evidence — every scored row can be traced back to one."

### Shot 4 — Pass/fail, field by field (1:30–2:20)

`[LIVE FOOTAGE: the scored table for that trap. One provider row shows
PASS on status and every scored field. The second provider row shows
FAIL with the mismatching field highlighted — a wrong status, or a
missing field. If the live run produces no failure, use the honest
variant in §3 instead of staging one.]`

> **Narration:** "Scoring is strict. Status must match exactly — a
> status mismatch fails the trap outright. Every scored field must
> match, and a missing field is a failure, never a pass. Here, one
> provider passes. The other fails, and you can see exactly which
> field it got wrong."

### Shot 5 — Leaderboard re-ranks (2:20–2:55)

`[LIVE FOOTAGE: the leaderboard page before and after this trap's
scores land. The failing provider's pass rate drops and its rank
moves. Show the ranking rule on screen: pass rate, then traps run,
then lower total testnet cost.]`

> **Narration:** "The leaderboard re-ranks on the new evidence.
> Pass rate first, then traps run, then lower cost. A provider that
> returns a stale or wrong answer does not stay at the top — it is
> shown failing, with its receipt, for any builder choosing a
> provider to see."

### Shot 6 — Reproduce it yourself (2:55–3:30)

On screen: the how-to-run steps (text, no footage needed beyond the
repo page).

> **Narration:** "And a reviewer can repeat this. The trap set is
> frozen before scoring, the ground truth is public, and the same
> loop runs with a new trap input — receipts included. TrapTest does
> not ask you to trust a ranking. It shows you the receipts."
>
> **On-screen closing text:** "TrapTest — Telegraph Hackathon
> Season II. Testnet evaluation only. No independent adoption is
> claimed. [FILL at recording: repo link.]"

## 2. Recording checklist (event window only)

- [ ] Day-1 gates passed (prize terms, free testnet funds, competing
      supply re-confirmed, Evaluator wording confirmed) — see
      `docs/how-to-run.md` §5. Do not record a live run before they pass.
- [ ] Trap set frozen and committed before the first scored purchase;
      freeze date visible in the recording or the repo.
- [ ] At least two competing providers bought for the demo trap, with
      receipts on screen (cost, signal hash, receipt id). Blur nothing
      that a reviewer needs to verify; show no keys or wallet secrets.
- [ ] Failure case visible on screen (see §3 for the honest fallback).
- [ ] Captions on; narration matches the on-screen evidence exactly.
      If the live result differs from this script's example wording
      (e.g. which field failed), re-record the narration — never
      re-cut the footage to fit the script.
- [ ] Length checked: 2–5 min. No mock footage in the submitted cut;
      any mock reference shot is cut before submission.

## 3. Honest variants — use these, never stage a result

- **No provider fails in the live run:** replace Shot 4's fail
  narration with: "In this run, both providers passed this trap.
  The leaderboard still re-ranks on pass rate and cost — and a run
  with no failures is a weaker result, which is why the full trap set
  includes reverted and not-found traps designed to catch providers
  that invent or misreport." Show the reverted and not-found trap
  rows from the full run `[LIVE FOOTAGE]` if either produced a fail;
  if neither did, say so and stop there.
- **A provider's answer cannot be mapped to the scorer's fields:**
  do not present it as a lie. Show it as "unmapped schema, not scored
  as a lie" (see `docs/judge-review.md` Risk 2) and narrate that
  distinction on screen.
- **Only one provider answers:** do not present a one-provider table
  as a leaderboard. The video must say the comparison could not be
  run, and the submission must use the scored-table fallback or the
  Sentinel fallback decision from the judge review — never a
  dressed-up single-provider result.

## 4. What this script deliberately does not claim

- No provider name, pass rate, cost figure, or accuracy number — all
  are `[FILL]` from the live run only.
- No adoption, user, retention, or demand claim. The closing text
  states the honest position: testnet evaluation by the author,
  no independent adoption claimed.
- No mainnet claim: everything shown is Base Sepolia testnet.
