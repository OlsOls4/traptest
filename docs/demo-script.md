# TrapTest — demo script (RE-CUT v2, 8 Nov 2026)

**Status: RE-CUT v2, 8 Nov 2026. Video: `docs/demo-video/traptest-demo-2026-11-08.mp4`
(2:42, 1280×720, local file only — DO NOT upload). Narration script +
storyboard: `docs/demo-video/narration.md`. Numbers are from the live run
(`results-live/full-run-2026-11-06.json`, 60 rows) as corrected by the
disclosed re-score (`results-live/results-corrected-2026-11-08.json`:
Truvian 4/12, strict original 3/12). No mock footage in the submitted cut.
v1 (`traptest-demo-2026-11-06.mp4`, 2:36) is kept intact.**

Target length: **2:42** (must be 2–5 min). One voice, plain narration,
captions on. No music bed over narration. No claim about adoption,
users, accuracy, or money saved — none exists yet.

## 0. The 60-second judge path (the spine of the whole video)

One trap input → competing answers bought on testnet → pass/fail with
receipts → leaderboard re-ranks, with a stale/wrong answer failing on
screen. Everything else in the video is set-up for, or payoff from,
that path. If a viewer watches only the first 60 seconds, they must
have seen: what a trap is, two providers answering the same trap, and
at least one pass and one fail (or, if no provider fails in the live
run, an honest on-screen note saying so — see §3). In v2 the verdict
lands at ~0:48 ("Different answers", end of Shot 3's verdict block).

## 1. Storyboard and narration

### Shot 1 — Hook (0:00–0:14) — no footage needed

On screen: the TrapTest title and one sentence.

> **Narration:** "Telegraph ranks AI providers by intelligence. But who
> checks whether the ranking itself can be trusted? TrapTest does.
> It buys the same question from competing providers — a question
> whose answer is already known — and shows you who got it right."

### Shot 2 — What a trap is (0:14–0:33) — screen capture of the trap file

`[LIVE FOOTAGE: trap file — trap id, intent ONCHAIN_TX_LOOKUP_GENERAL, tx hash,
expected status, from, to, value, block, and the public-chain source
link for the ground truth. No provider answer visible yet.]`

> **Narration:** "A trap is a transaction query with known ground
> truth. Its sender, recipient, value and block were checked against
> the public chain record before any provider was scored — so the truth
> never comes from a provider's own answer. Twelve traps like this were
> frozen on the 6th of November, before a single purchase was made."

### Shot 3 — One input, two competing buys (0:33–1:06)

`[LIVE FOOTAGE: the runner buying the trap from two competing providers
via Direct Ask, one miner at a time. Show the two request rows and the
Telegraph receipts as they land: cost_usd, signal_hash, and
X-TELEGRAPH-RECEIPT per call. Do not show any wallet, key, or seed.
In v2 the Truvian box shows the real truncated t07 signal hash
0x1e082282cb167180…60d285 and receipt hash 0xb7f772e31a8722bb…1b3d95.]`

> **Narration:** "Take one trap: a reverted transaction. TxLens
> answers: not found. It says that about every mined transaction we
> asked it. Truvian answers: reverted — with the right block, sender
> and recipient. Same question, same price. Different answers.
> TrapTest buys each trap from competing providers, one at a time,
> through Telegraph's Direct Ask. Every served call costs one cent of
> testnet USDC, and comes back with a signal hash and a Telegraph
> receipt — the evidence behind every scored row."

### Shot 4 — Pass/fail, field by field (1:06–1:42)

`[LIVE FOOTAGE: the scored table for that trap. One provider row shows
PASS on status and every scored field. The second provider row shows
FAIL with the mismatching field highlighted — a wrong status, or a
missing field. If the live run produces no failure, use the honest
variant in §3 instead of staging one. In v2 TxLens shows FAIL on
every scored field (status not_found, from/to/block null in the live
t07 row) — the v1 "fails on status alone" line was wrong.]`

> **Narration:** "Scoring is strict. Status must match exactly — a
> wrong status fails the trap outright, and a missing field is a
> failure, never a pass. TxLens fails this trap on every scored field
> — it answered not found and returned nothing else. Truvian passes it
> outright. And here is the honest part. Truvian fails other traps,
> not because it got the transaction wrong — its block, sender,
> recipient and value were all right — but because it reports no status
> at all for confirmed transactions. Under strict scoring that is still
> a fail. We show the gap. We don't hide it, and we don't call it a
> lie."

### Shot 5 — Leaderboard re-ranks (1:42–2:21)

`[LIVE FOOTAGE: the leaderboard page before and after this trap's
scores land. The failing provider's pass rate drops and its rank
moves. Show the ranking rule on screen: pass rate, then traps run,
then lower total testnet cost. In v2 the ranked table is drawn from
the corrected re-score (Truvian 4/12, strict original 3/12) with
provider names beside IDs, the correction note, the $0.24 escrow
line, and the small-sample caveat on screen.]`

> **Narration:** "Across all twelve traps, Truvian passed four,
> TxLens passed two — a corrected re-score; the strict original was
> three. Four versus two is two traps — evidence, not a verdict on
> provider quality. Three more providers couldn't serve this intent at
> all. LiveCert answered every call with a 503. Sigil and OnChain
> Intel failed upstream on all twelve — and those failed calls were
> not billed: twenty-four cents settled into Telegraph escrow credit
> instead. The leaderboard ranks on pass rate first, then traps run,
> then cost. A provider that returns a stale or wrong answer doesn't
> stay at the top."

### Shot 6 — Reproduce it yourself (2:21–2:42)

On screen: the how-to-run steps (text, no footage needed beyond the
repo page).

> **Narration:** "And a reviewer can repeat this. The trap set is
> frozen, the ground truth is public, and the same loop runs with a new
> trap input — receipts included. TrapTest doesn't ask you to trust a
> ranking. It shows you the receipts. TrapTest — Telegraph Hackathon
> Season Two. Testnet evaluation only. No independent adoption is
> claimed."
>
> **On-screen closing text:** "TrapTest — shows you the receipts.
> Testnet evaluation only. No independent adoption is claimed."
> Repo: https://github.com/OlsOls4/traptest

## 2. Recording checklist (event window only) — all DONE 6 Nov 2026

- [x] Day-1 gates passed (prize terms still unpublished — stated
      plainly; free testnet funds resolved via open mint + PoW faucet;
      competing supply re-confirmed; Evaluator wording still open —
      see `docs/how-to-run.md` §5).
- [x] Trap set frozen and committed before the first scored purchase;
      freeze date visible in the recording or the repo.
- [x] At least two competing providers bought for the demo trap, with
      receipts on screen (cost, signal hash, receipt id). Blur nothing
      that a reviewer needs to verify; show no keys or wallet secrets.
- [x] Failure case visible on screen (TxLens `not_found` on a confirmed
      tx; Truvian missing-status schema gap shown honestly).
- [x] Captions on; narration matches the on-screen evidence exactly.
- [x] Length checked: 2:42 (2–5 min). No mock footage in the submitted cut.

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

- No provider name, pass rate, cost figure, or accuracy number beyond
  the live run's, as corrected: Truvian 4/12 corrected (strict 3/12),
  TxLens 2/12, LiveCert/Sigil/OnChain Intel 0/12 served 0, billed $0.24
  + $0.24 escrow credit, 60 rows — all from
  `results-live/full-run-2026-11-06.json` and the disclosed re-score in
  `results-live/results-corrected-2026-11-08.json`.
- No adoption, user, retention, or demand claim. The closing text
  states the honest position: testnet evaluation by the author,
  no independent adoption claimed.
- No mainnet claim: everything shown is Base Sepolia testnet queries
  with settlement on Ethereum Sepolia testnet.
