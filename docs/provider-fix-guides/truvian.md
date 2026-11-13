# Truvian (8453): two small fixes that change your TrapTest score

TrapTest buys fixed trap transaction queries — questions whose ground truth is known in advance — from competing `ONCHAIN_TX_LOOKUP_GENERAL` providers on Telegraph testnet, and scores each answer pass/fail. Your current scores, both live on the leaderboard (https://olsols4.github.io/traptest/docs/leaderboard/):

- **Frozen set (12 traps, 6 Nov 2026, corrected re-score 8 Nov): 4/12**, field accuracy 37/47. (Strict original: 3/12 — the correction is a disclosed re-score of the same raw answers; one trap, t08, was scored FAIL though your value `1e-05` ETH equals the expected 10000000000000 wei.)
- **Expansion set (12 traps, 9 Nov 2026): 2/12**, field accuracy 39/49.

The 2/12 pass rate understates your answers. On the expansion set, 8 of your 10 fails are a missing `status` field alone — traps t13, t14, t15, t16, t19, t20, t21 and t22, where your `from`, `to`, `value` and `block` are all correct and only `status` is absent (null). The other two fails, t23 and t24 (unknown transactions), are a different single-field issue: your `from` field carries the string "Truvian onchain lookup over public JSON-RPC" — a provenance label, not a sender address — and the expansion set's strict-unknown rule fails any `not_found` answer that carries an invented detail field.

## Fix 1 — return `status` for confirmed transactions

Add `status` (`confirmed` / `reverted` / `not_found`) to every answer. On the expansion set this alone moves you from 2/12 to **10/12**; on the frozen set it moves you from 4/12 to **10/12** (six of the eight frozen fails are a missing `status` alone). This is a schema gap, not a wrong answer: your transaction data is right, the field is just absent, and strict scoring counts a missing field as a failure.

## Fix 2 — move the provenance label out of `from`

Put "Truvian onchain lookup over public JSON-RPC" in its own field (for example `source` or `provenance`) and return `from: null` when the answer is `not_found`. With Fix 1, this moves the expansion set from 10/12 to **12/12** (t23 and t24 then pass: their `status` is already correct). It changes nothing on the frozen set — the frozen unknown traps (t11, t12) already pass, because the frozen scoring version skips fields with no expected value.

One thing we are not asking you to change: the frozen t03/t04 value fails. Those traps score the Transfer event amount as `value`, which no provider returns in the intent's `value_eth` field (native tx value). The expansion set already fixed that semantics — token traps there score the native value — so there is nothing for you to fix on t03/t04.

## Re-run offer (dated)

If you make either fix, we will re-run the 12-trap expansion set against Truvian (12 traps × $0.01 = **$0.12**, testnet USDC, our cost) and publish the new score beside the old one on the leaderboard — old score kept, not overwritten. Offer made 13 Nov 2026; re-run to be scheduled before the hackathon deadline of 1 Dec 2026 23:59 UTC.

## Dispute / correction route

If any of the above is wrong — a trap's ground truth, a scored field, or the reading of your answers — reply in Discord #hackathon or open a GitHub issue on https://github.com/OlsOls4/traptest with the trap ID and the correction. Every scored row (raw answer, normalised answer, per-field results, receipt) is in the repo's results files, so a dispute can be checked field by field. If a trap's ground truth is wrong, the honest move is to retire that trap and disclose it, not to quietly re-score it.

## Sources (every figure)

- Expansion 2/12, field accuracy 39/49; status-excluded view 10/12, 8 fails only on status: `docs/leaderboard/results-expansion.json` (`table`, `field_accuracy`, `sensitivity_status_excluded`).
- t23/t24 `from` label and strict-unknown rule: `docs/leaderboard/results-expansion.json` (`scoring_semantics`; t23/t24 rows, answer `from`: "Truvian onchain lookup over public JSON-RPC"); `traptest/scoring.py` (v2 strict-unknown rule).
- Frozen 4/12 corrected (strict 3/12), field accuracy 37/47; t08 normalisation fix: `docs/leaderboard/results.json` (`corrected`, `field_accuracy_corrected`, `methodology`).
- Frozen six-of-eight fails only on status: `docs/how-to-run.md` §2 ("Truvian fails 8, six of them only on a missing `status`"); verified against `results.json` corrected rows.
- t03/t04 value semantics (Transfer-event amount, unwinnable as specified; v2 scores native value): `docs/leaderboard/results.json` (`value_excluded_view` methodology); `docs/leaderboard/results-expansion.json` (`scoring_semantics`).
- Re-run cost $0.12 = 12 × $0.01: verified $0.01/call price (`docs/how-to-run.md` §3; expansion run billed $0.36 for 36 calls, `results-live/expansion-clean-run-2026-11-09.json`).
- Deadline 1 Dec 2026 23:59 UTC: brief (Telegraph Hackathon Season II).
