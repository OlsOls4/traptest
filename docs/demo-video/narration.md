# TrapTest — demo video: narration script + storyboard (v2, 8 Nov 2026)

**Status: RE-CUT 8 Nov 2026 (v2) from the live run + disclosed corrected
re-score. Every number below is from `results-live/full-run-2026-11-06.json`
(60 rows, LIVE) and `results-live/results-corrected-2026-11-08.json`
(corrected re-analysis; strict original preserved there verbatim).
No mock footage. Video file: `traptest-demo-2026-11-08.mp4` in this folder.
Local file only — DO NOT upload anywhere. v1
(`traptest-demo-2026-11-06.mp4`, 2:36) is kept intact in this folder.**

Core message: Telegraph ranks AI providers. TrapTest buys the same
known-answer question from competing providers and shows who got it
right — with receipts.

Target length 2:42 (must be 2–5 min). Final file 2:42 (161.6 s) — inside
the range. One voice (TTS, natural pace), burned captions on every shot.
No music bed over narration. Shot boundaries below are the actual v2
boundaries from the MP3 durations (s1 14.2 s, s2 18.3 s, s3 33.4 s,
s4 36.2 s, s5 38.5 s, s6 21.0 s).

## Shot 1 — Hook (0:00–0:14) — title card

On screen: "TrapTest" + "Who checks the ranking?" + "Telegraph
Hackathon Season II · Evaluator track".

> Narration: "Telegraph ranks AI providers by intelligence. But who
> checks whether the ranking itself can be trusted? TrapTest does. It
> buys the same question from competing providers — a question whose
> answer is already known — and shows you who got it right."

## Shot 2 — What a trap is (0:14–0:33) — frozen trap card (t01)

On screen: t01-plain-transfer fields — intent
ONCHAIN_TX_LOOKUP_GENERAL, tx 0xd47a09…ae96, expected status confirmed,
from 0xdead…0001, to 0x4200…0015, value 0, block 53047427; "Frozen
6 Nov 2026 13:59 UTC, before any purchase. Ground truth: Base Sepolia
public RPC."

> Narration: "A trap is a transaction query with known ground truth.
> Its sender, recipient, value and block were checked against the
> public chain record before any provider was scored — so the truth
> never comes from a provider's own answer. Twelve traps like this
> were frozen on the 6th of November, before a single purchase was
> made."

## Shot 3 — One input, competing buys (0:33–1:06) — t07 comparison

On screen: trap t07-reverted-tx. TxLens (9002): status "not_found" —
FAIL, $0.01, receipt present. Truvian (8453): status "reverted",
block / from / to all match — PASS, $0.01, receipt present, with the
real truncated hashes on screen: signal 0x1e082282cb167180…60d285,
receipt 0xb7f772e31a8722bb…1b3d95 (full values in
`results-live/full-run-2026-11-06.json`, t07 Truvian row).
"Same question · Same price · Different answers."
The PASS/FAIL verdict ("Different answers") lands at ~0:48 — inside
the first 60 seconds.

> Narration: "Take one trap: a reverted transaction. TxLens answers:
> not found. It says that about every mined transaction we asked it.
> Truvian answers: reverted — with the right block, sender and
> recipient. Same question, same price. Different answers. TrapTest
> buys each trap from competing providers, one at a time, through
> Telegraph's Direct Ask. Every served call costs one cent of testnet
> USDC, and comes back with a signal hash and a Telegraph receipt —
> the evidence behind every scored row."

## Shot 4 — Pass/fail, field by field (1:06–1:42) — t07 field table

On screen: t07 field table (status / from / to / block): TxLens ✗ ✗ ✗
✗ → FAIL (it answered not_found and returned nothing else — from, to
and block are all null in the live row); Truvian ✓ ✓ ✓ ✓ → PASS.
Note below: "Truvian on confirmed txs: block, from, to, value all
correct — status blank → strict FAIL (schema gap, not a wrong
answer)."

> Narration: "Scoring is strict. Status must match exactly — a wrong
> status fails the trap outright, and a missing field is a failure,
> never a pass. TxLens fails this trap on every scored field — it
> answered not found and returned nothing else. Truvian passes it
> outright. And here is the honest part. Truvian fails other traps,
> not because it got the transaction wrong — its block, sender,
> recipient and value were all right — but because it reports no
> status at all for confirmed transactions. Under strict scoring that
> is still a fail. We show the gap. We don't hide it, and we don't
> call it a lie."

## Shot 5 — Leaderboard re-ranks (1:42–2:21) — corrected ranked table

On screen: ranked table drawn from the corrected re-score
(`results-live/results-corrected-2026-11-08.json`), with provider
names beside IDs: 1. Truvian 8453 — 33%, 4/12, $0.12, 12/12 receipts;
2. TxLens 9002 — 17%, 2/12, $0.12, 12/12 receipts; LiveCert 4433,
Sigil 9010, OnChain Intel 900 — unservable, 0 served, $0.00 billed.
Note below: "Corrected 8 Nov: Truvian 4/12 (strict original 3/12),
t08 normalisation fix." + "Failed calls were not billed: $0.24
settled into Telegraph escrow credit." + "Four versus two is two
traps — evidence, not a verdict on provider quality."

> Narration: "Across all twelve traps, Truvian passed four, TxLens
> passed two — a corrected re-score; the strict original was three.
> Four versus two is two traps — evidence, not a verdict on provider
> quality. Three more providers couldn't serve this intent at all.
> LiveCert answered every call with a 503. Sigil and OnChain Intel
> failed upstream on all twelve — and those failed calls were not
> billed: twenty-four cents settled into Telegraph escrow credit
> instead. The leaderboard ranks on pass rate first, then traps run,
> then cost. A provider that returns a stale or wrong answer doesn't
> stay at the top."

## Shot 6 — Reproduce it yourself (2:21–2:42) — how-to-run card

On screen: `python3 scripts/full_run.py` / `python3 scripts/mini_run.py`
— frozen trap set + burner flow, `docs/how-to-run.md`. Closing text:
"TrapTest — shows you the receipts. Testnet evaluation only. No
independent adoption is claimed."

> Narration: "And a reviewer can repeat this. The trap set is frozen,
> the ground truth is public, and the same loop runs with a new trap
> input — receipts included. TrapTest doesn't ask you to trust a
> ranking. It shows you the receipts. TrapTest — Telegraph Hackathon
> Season Two. Testnet evaluation only. No independent adoption is
> claimed."

## Evidence notes (for the submission pack)

- Truvian 8453: CORRECTED 4/12 (t07, t08, t11, t12); strict original
  3/12 (t07, t11, t12). The correction is a disclosed re-score:
  t08 was scored FAIL though Truvian's value_eth 1e-05 equals the
  expected 10000000000000 wei (normalisation fix). Field accuracy
  corrected 37/47 (strict 36/47). Ranking order unchanged.
- TxLens 9002: 2/12 (passed t11, t12 unknown-tx — not_found is correct
  there); answered not_found for all 10 mined txs. Field accuracy 2/47.
  On t07 every scored field fails (status not_found, from/to/block null).
- LiveCert 4433: 0/12 served — 503 no_compatible_miner on all 12, $0.
- Sigil 9010: 0/12 served — HTTP 500 upstream 404 on all 12; $0.01/call
  settled on-chain into Telegraph escrow credit, not billed ($0.12).
- OnChain Intel 900: 0/12 served — HTTP 500 upstream 400 "Could not
  determine a supported chain" (upstream still on old ONCHAIN_TX_LOOKUP
  intent); $0.01/call settled into escrow credit, not billed ($0.12).
- Session accounting: billed $0.26 (smoke $0.02 + full run $0.12 +
  Truvian $0.12); escrow credit $0.24; wallet 30.00 → 29.50 test USDC
  (drop $0.50, verified on-chain). Session cap $0.50 not exceeded on
  billed spend; out-of-wallet total is exactly $0.50 including escrow
  credit held by Telegraph.

## v2 changes vs v1 (8 Nov 2026)

- Shot 4 fixed: TxLens from/to/block now ✗ (live row has them null),
  narration now "fails this trap on every scored field".
- Shot 5 rebuilt as a drawn corrected table (the v1 leaderboard
  screenshot in /tmp no longer exists; the page renders IDs only,
  strict 3/12, and cost 0.0000 for unservable providers): provider
  names, corrected 4/12 vs 2/12, strict-original note, escrow line,
  small-sample caveat on screen and narrated.
- Shot 3 shows one real truncated signal + receipt hash on the Truvian
  box (t07, verified prefix/suffix against the live JSON).
- Shot 2 trimmed by dropping the block-number sentence (frame still
  shows block 53047427); Shot 3 reordered verdict-first, so the
  PASS/FAIL verdict lands at ~0:48, inside 60 s.
- Shot 5 narration adds the corrected re-score, the caveat, and the
  $0.24 escrow finding.
