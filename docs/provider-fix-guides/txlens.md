# TxLens (9002): your answers say `not_found` for transactions that exist

TrapTest buys fixed trap transaction queries — questions whose ground truth is known in advance — from competing `ONCHAIN_TX_LOOKUP_GENERAL` providers on Telegraph testnet, and scores each answer pass/fail. Your current scores, both live on the leaderboard (https://olsols4.github.io/traptest/docs/leaderboard/):

- **Frozen set (12 traps, 6 Nov 2026): 2/12**, field accuracy 2/47.
- **Expansion set (12 traps, 9 Nov 2026): 2/12**, field accuracy 2/47.

Both passes are the unknown-transaction traps (frozen t11, t12; expansion t23, t24), where `not_found` is the correct answer. Every mined transaction we asked about — 10 of 10 on each set, across plain transfers, token transfers, contract interactions, reverted transactions and multi-recipient transactions — came back `not_found`, with `from`, `to`, `value` and `block` all null.

That is not a schema gap. A missing field that the provider otherwise gets right is a gap; an answer of `not_found` for a mined, confirmed transaction is a wrong answer. For contrast, on the same expansion traps Truvian got 39 of 49 fields right and ChainWire 46 of 47 — the transactions are served by other providers, so the ground truth is not the problem. Your two passes also show the lookup itself can return the right status when the answer is `not_found`; the failure is specific to mined transactions.

## What would fix it

Serve mined transactions: return `confirmed` or `reverted` with the correct `from`, `to`, `value` and `block` for transactions that exist on Base Sepolia. There is no smaller fix to offer — no single field addition changes the score, because every mined-trap field fails together. If there is a chain or indexing reason (for example, the lookup is pointed at a different chain than Base Sepolia, or at an index that does not cover these blocks), that is the thing to check first: the trap transactions are all real Base Sepolia transactions, verified against the public Base Sepolia RPC before freezing.

## Re-run offer (dated)

If you change the behaviour, we will re-run the 12-trap expansion set against TxLens (12 traps × $0.01 = **$0.12**, testnet USDC, our cost) and publish the new score beside the old one on the leaderboard — old score kept, not overwritten. Offer made 13 Nov 2026; re-run to be scheduled before the hackathon deadline of 1 Dec 2026 23:59 UTC.

## Dispute / correction route

If any of the above is wrong — a trap's ground truth, a scored field, or the reading of your answers — reply in Discord #hackathon or open a GitHub issue on https://github.com/OlsOls4/traptest with the trap ID and the correction. Every scored row (raw answer, normalised answer, per-field results, receipt) is in the repo's results files, so a dispute can be checked field by field. If a trap's ground truth is wrong, the honest move is to retire that trap and disclose it, not to quietly re-score it.

## Sources (every figure)

- Frozen 2/12 (t11, t12 only), field accuracy 2/47: `docs/leaderboard/results.json` (`corrected` table, `field_accuracy_corrected`).
- Expansion 2/12 (t23, t24 only), field accuracy 2/47: `docs/leaderboard/results-expansion.json` (`table`, `field_accuracy`); per-row answers show `status: not_found` with all other fields null on all 10 mined expansion traps.
- "Answers `not_found` for every mined tx": `docs/how-to-run.md` §2 ("TxLens fails 10 traps on a wrong `status` — it answers `not_found` for every mined tx"); verified against the per-row data in both results files.
- Truvian 39/49, ChainWire 46/47 (expansion): `docs/leaderboard/results-expansion.json` (`field_accuracy`).
- Ground truth source (Base Sepolia public RPC): `anjoman-material/truth-source.yaml`; `traps-frozen-2026-11-06.json` / `traps-frozen-2026-11-09.json` (provenance per trap).
- Re-run cost $0.12 = 12 × $0.01: verified $0.01/call price (`docs/how-to-run.md` §3; expansion run billed $0.36 for 36 calls, `results-live/expansion-clean-run-2026-11-09.json`).
- Deadline 1 Dec 2026 23:59 UTC: brief (Telegraph Hackathon Season II).
