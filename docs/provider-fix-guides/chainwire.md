# ChainWire (1707307, Cross-Checked): what you do right, and the one miss

TrapTest buys fixed trap transaction queries — questions whose ground truth is known in advance — from competing `ONCHAIN_TX_LOOKUP_GENERAL` providers on Telegraph testnet, and scores each answer pass/fail. Your current score, live on the leaderboard (https://olsols4.github.io/traptest/docs/leaderboard/):

- **Expansion set (12 traps, 9 Nov 2026): 11/12**, field accuracy 46/47.

Note on scope: ChainWire ran the expansion set only — there is no frozen-set score for ChainWire, and no combined 24-trap number. The 11/12 is on the 12 expansion traps.

## What you do right

You return a complete answer on every trap, including `status` — the field the other providers miss. On the expansion set you returned the correct `status` on all 12 traps, including `reverted` on both reverted-transaction traps (t17, t18), and the correct `from`, `to` and `block` throughout. That is why the ranking order is stable across every view we publish: strict pass rate, field accuracy, and the status-excluded sensitivity view all put ChainWire first. For comparison on the same 12 traps, Truvian passed 2/12 (39/49 fields) and TxLens passed 2/12 (2/47 fields). Your answers diverge from Truvian's on 11 of the 12 traps and from TxLens's on 9 of 12 — the expansion set is genuinely discriminating between providers, and you are on the right side of that discrimination.

## The one miss — t17 (reverted transaction)

Trap t17 is a reverted transaction. You returned the right `status` (`reverted`), the right `from`, the right `to` and the right `block` — and `value` 0 where the ground truth is 607000000000000 wei. That single field is the difference between 11/12 and 12/12, and between 46/47 and 47/47. It is the only field you missed across the whole set. If your value lookup reads the native transaction value, this one is worth checking against the receipt: the trap's ground truth was verified against the public Base Sepolia RPC before freezing, and the same value is what Truvian returned correctly on this trap.

## Re-run offer (dated)

If you change the behaviour, we will re-run the 12-trap expansion set against ChainWire (12 traps × $0.01 = **$0.12**, testnet USDC, our cost) and publish the new score beside the old one on the leaderboard — old score kept, not overwritten. Offer made 13 Nov 2026; re-run to be scheduled before the hackathon deadline of 1 Dec 2026 23:59 UTC.

## Dispute / correction route

If any of the above is wrong — the t17 ground truth, a scored field, or the reading of your answers — reply in Discord #hackathon or open a GitHub issue on https://github.com/OlsOls4/traptest with the trap ID and the correction. Every scored row (raw answer, normalised answer, per-field results, receipt) is in the repo's results files, so a dispute can be checked field by field. If a trap's ground truth is wrong, the honest move is to retire that trap and disclose it, not to quietly re-score it.

## Sources (every figure)

- Expansion 11/12, field accuracy 46/47: `docs/leaderboard/results-expansion.json` (`table`, `field_accuracy`).
- ChainWire ran expansion only, no combined number: `docs/leaderboard/results-expansion.json` (`combined_24_trap_note`).
- t17 row (status/from/to/block correct, value expected 607000000000000, actual 0): `docs/leaderboard/results-expansion.json` (t17, provider 1707307); `results-live/expansion-clean-run-2026-11-09.json` (same row; 36 calls, $0.36, 36/36 receipts verified on-chain).
- Ranking stable across all three views; divergence 11 vs Truvian, 9 vs TxLens: `docs/leaderboard/results-expansion.json` (`sensitivity_note`); `docs/leaderboard/index.html` ("ChainWire 1707307 diverges from Truvian on 11 traps and from TxLens on 9"); recomputed from the scores during drafting (same result).
- Truvian 2/12 (39/49), TxLens 2/12 (2/47): `docs/leaderboard/results-expansion.json` (`table`, `field_accuracy`).
- Truvian returned the t17 value correctly: `docs/leaderboard/results-expansion.json` (t17, provider 8453: value 607000000000000, passed).
- Re-run cost $0.12 = 12 × $0.01: verified $0.01/call price (`docs/how-to-run.md` §3; expansion run billed $0.36 for 36 calls).
- Deadline 1 Dec 2026 23:59 UTC: brief (Telegraph Hackathon Season II).
