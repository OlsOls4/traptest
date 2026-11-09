# Verification note — expansion preference pairs (t13–t24)

Prepared 9 Nov 2026. Local file only — NOT uploaded to Anjoman.
Companion to `preference-pairs-expansion.jsonl` (12 lines, t13–t24 in order).

## Sources (read-only; none modified)

- Frozen ground truth: `../traps-frozen-2026-11-09.json`
  (frozen 9 Nov 2026 13:07:38Z, sha256
  `940a00400477e0aefb38afe1da20fb98cc03b187e7218da252d322fd4699b5ba` — re-checked
  after the build, unchanged). Scoring v2: token traps score the NATIVE tx value;
  unknown-tx traps carry the strict rule (a `not_found` answer with any invented
  from/to/value/block fails outright).
- Rejected answers — SOLE source: `../results-live/expansion-clean-run-2026-11-09.json`,
  run `run-20261109T162426Z-56816b` (single-file clean re-run, 36 rows;
  ChainWire 1707307 11/12, Truvian 8453 2/12, TxLens 9002 2/12; 36/36 receipts
  verified on-chain at write time). Nothing was taken from the stitched
  expansion-run files, and no rejected answer was invented.
- Prompt format: derived mechanically per category from the submitted v1 file
  (`preference-pairs.submitted-v1.jsonl` + `traps-frozen-2026-11-06.json`) —
  same prompt wording as v1, only the tx hash changed.
- Token Transfer amounts in the chosen answers (t13: 3000000, t14:
  8505385980000000000 raw token units) come from the frozen provenance notes
  and were cross-checked against the first Transfer log in the second-RPC
  receipt transcript (`results-live/ground-truth-recheck-2026-11-09.json`).

## Per-trap rejected provider (all real, all failed that trap in the clean run)

| Trap | Category | Rejected provider | Why it is wrong |
|---|---|---|---|
| t13 | token transfer | TxLens 9002 | Answered `not_found` (all fields null) for a confirmed tx |
| t14 | token transfer | TxLens 9002 | Answered `not_found` (all fields null) for a confirmed tx |
| t15 | contract interaction | TxLens 9002 | Answered `not_found` (all fields null) for a confirmed tx |
| t16 | contract interaction | TxLens 9002 | Answered `not_found` (all fields null) for a confirmed tx |
| t17 | reverted tx | ChainWire 1707307 | Value `0` instead of 607000000000000 wei; status/from/to/block all correct — the near-miss, and the only trap ChainWire failed |
| t18 | reverted tx | TxLens 9002 | Answered `not_found` (all fields null) for a reverted tx |
| t19 | multi-recipient | TxLens 9002 | Answered `not_found` (all fields null) for a confirmed tx |
| t20 | multi-recipient | TxLens 9002 | Answered `not_found` (all fields null) for a confirmed tx |
| t21 | plain transfer | TxLens 9002 | Answered `not_found` (all fields null) for a confirmed tx |
| t22 | plain transfer | TxLens 9002 | Answered `not_found` (all fields null) for a confirmed tx |
| t23 | unknown tx | Truvian 8453 | Status `not_found` is right, but it invented a `from` field — the literal string "Truvian onchain lookup over public JSON-RPC" (not an address) — violating the strict-unknown rule. The only wrong answer for this trap (ChainWire and TxLens both passed cleanly) |
| t24 | unknown tx | Truvian 8453 | Same invented-`from` defect as t23; again the only wrong answer for the trap |

No trap lacked a real wrong answer: every trap has at least one failing provider
in the clean run, so all 12 lines are present — no gaps, no fabricated rejected.
No numerically-correct answer is used as a rejected: the TxLens `not_found`
answers are wrong on every field; ChainWire's t17 value is numerically wrong;
Truvian's t23/t24 answers fail the strict-unknown rule outright. (Truvian's
missing-status answers were NOT used: TxLens's confidently-wrong status is the
more instructive contrast on those traps, matching the v1 pattern.)

## Deliberate wording deviations from v1 (both honest, both verified)

1. **Multi-recipient chosen (t19/t20): "Recipient:" instead of v1's "First
   recipient:".** In v1 the frozen `to` WAS the first Transfer recipient. In the
   expansion set the frozen `to` is the called contract, not a Transfer
   recipient (verified against the second-RPC receipt transcript: t19's first
   Transfer goes to 0x0dac47d5…, t20's to 0xc4ef24cd…, neither equals the frozen
   `to`). Calling it "First recipient" would be false. The chosen states the
   frozen tx `to` as "Recipient:" plus the frozen count ("3 Transfer events to
   3 distinct recipients").
2. **Token chosen (t13/t14): v1 wording kept verbatim** ("Token transfer amount:
   … Native transaction value: 0 wei."). Under scoring v2 the native value
   (0 wei) is the scored value and the Transfer amount is unscored context —
   the text is true under both semantics, so no rewording was needed.

## Verification result

Verifier: `/tmp/verify_expansion.py` (re-runnable), exit 0 — ALL CHECKS PASSED:

- 12 lines, every line valid JSON, keys exactly `prompt`/`chosen`/`rejected`
  (in that order), no extra keys, no empty values, chosen ≠ rejected;
  prompt lengths 166–215 chars, chosen/rejected inside the docs' limits
  (prompt 16–16,000; chosen/rejected 8–32,000).
- Tx hashes t13–t24 in frozen-file order in every prompt.
- Chosen checked field by field against the frozen ground truth — status, from,
  to, value where scored (native value for token traps), block; token Transfer
  amount + contract; multi-recipient Transfer count; unknown traps state
  `not_found` with no invented fields. Zero mismatches.
- Rejected checked against the clean run file's stored answers — for every trap
  the named provider's stored row has `passed: false`, and every value rendered
  in the rejected text matches that row's stored normalised answer verbatim
  (TxLens null-field `not_found`; ChainWire t17 status/from/to/value `0`/block;
  Truvian t23/t24 invented `from` string verbatim).
- Sources untouched: frozen trap file sha256 still `940a0040…`, clean-run run id
  / sha / tally unchanged, v1 pairs files and truth source unmodified
  (mtimes 6–8 Nov; only the two new files in this folder are new).

## Build scripts (kept outside this folder, in /tmp)

- `/tmp/build_expansion.py` — builds the file from the sources above.
- `/tmp/verify_expansion.py` — the independent verifier (re-run with
  `python3 /tmp/verify_expansion.py` after any edit).
