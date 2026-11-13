# Starter kit: reuse the trap format on a new intent

> ⚠️ The three `example-*` files in this folder are teaching examples only — never submit them to Anjoman as real evaluation material.

## What is in this folder

| File | What it is |
|---|---|
| `traps-template.json` | Generic trap-file template for `ONCHAIN_TX_LOOKUP_GENERAL` — required fields + inline notes. Replace every `<REPLACE-ME>`; delete `_template_notes` before freezing. |
| `example-onchain-metric-verify-trap.json` | ONE worked EXAMPLE trap for a different, illustrative intent (`ONCHAIN_METRIC_VERIFY` — not a real Telegraph intent). Block 56538934, 4 transactions. Not submitted anywhere. |
| `example-onchain-metric-verify-pair.jsonl` | ONE worked EXAMPLE preference pair (`prompt` / `chosen` / `rejected`) for that intent, in the same one-JSON-object-per-line format as `anjoman-material/preference-pairs.jsonl`. Not submitted anywhere. |
| `example-onchain-metric-verify-truth-source.yaml` | ONE worked EXAMPLE truth-source YAML (miner YAML v1) for that intent, in the same shape as `anjoman-material/truth-source.yaml`. Not submitted anywhere. |

## Steps (to build your own trap set for a new intent)

1. **Pick the intent and check it exists.** Look the intent up in the live Telegraph catalogue first. TrapTest's intent is `ONCHAIN_TX_LOOKUP_GENERAL`; the kit's example intent `ONCHAIN_METRIC_VERIFY` is invented for illustration — do not submit material for an intent name you have not verified in the catalogue.
2. **Define the scored fields.** For `ONCHAIN_TX_LOOKUP_GENERAL` the scored fields are `status, from, to, value, block` (see `traptest/scoring.py`). For a new intent, write down the equivalent list first — every scored field needs an expected value, a comparison rule (exact string? numeric? case-insensitive?), and a rule for what a missing field means. TrapTest's rule: a missing field is a failure, never a pass.
3. **Pick the trap categories.** TrapTest uses six categories for tx lookup (plain transfer, token transfer, contract interaction, reverted tx, multi-recipient tx, unknown tx) and requires at least one reverted tx and one unknown tx per set (`traptest/trap_design.md` §2, `traptest/trap_catalog.py`). A new intent needs its own category list — including at least one "should say not found / should refuse" category, the unknown-tx equivalent, or providers that hallucinate will pass uncaught.
4. **Verify ground truth per trap against public chain data.** Never copy ground truth from a provider's answer. TrapTest checks each trap against the Base Sepolia public RPC (`https://base-sepolia-rpc.publicnode.com`). Record provenance on every trap: source, source URL, block, checked-at time, checker, and notes (value basis, token contract, anything a reviewer needs to reproduce the check). `validate_provenance` rejects a set with missing or mismatched provenance.
5. **Freeze the set before buying anything.** Write the trap file, record the freeze time, and do not edit it after the first scored purchase. If a trap's ground truth later turns out wrong, retire the trap and disclose it — do not quietly re-score it.
6. **Dry-run, then buy small.** Validate with `--dry-run` (spends and writes nothing), then replay one trap against two providers before running a full set. Every served call should record cost, signal hash and receipt.
7. **Publish the score with the receipts beside it** — pass rate and field accuracy together, the strict rules stated, and the failures shown, not hidden.

## Time / cost checklist

- **Time — the trap checks, not the code.** The expensive part is hand-checking ground truth for every trap against the public RPC. TrapTest froze 12 traps per set after a per-trap RPC check plus provenance; budget your time there, not on the runner. No time figure is claimed here — TrapTest's own drafting time was not measured.
- **Cost — $0.01 per served call (testnet USDC).** Verified live price from the 402 challenge, not the catalogue's `cost_per_call` field. Budget: traps × providers × $0.01. Examples from TrapTest: 12 traps × 2 providers = $0.24 billed; 12 traps × 3 providers = $0.36 billed (expansion clean run, 36 calls). Per-run hard spend cap defaults to $0.30 (`traptest/run.py`).
- **Failed calls can still settle.** On the frozen set, 24 unserved calls settled $0.01 each ($0.24 total) into Telegraph escrow credit, not billed; 503 failures settled nothing. Budget the escrow possibility separately from billed cost, and reconcile the burner balance against billed + escrow, not billed alone.
- **Free steps:** inspecting trap files, checking ground truth on the public RPC, running the 165 unit tests, dry-running the loop, and reading the leaderboard all cost $0.
- **What you need before spending anything:** a disposable testnet-only burner key (never a real wallet, never mainnet), self-minted accepted test USDC (`0xcc194e1a843B658526D0D5C431f670028582Ae17` on Ethereum Sepolia — open mint, no Telegraph faucet exists) plus a little Sepolia ETH for the one-time mint. No card, purchase or bridge.

## What still needs scorer adaptation, and why

The current scorer only understands `ONCHAIN_TX_LOOKUP_GENERAL`. To score a new intent you must adapt, at minimum:

- **`traptest/traps.py` (`Trap` dataclass):** fields are `expected_status/from/to/value/block` plus `tx_hash`. A metric intent needs different expected fields (the example uses `block_number` + `expected_tx_count`). The dataclass, its validation (status must be one of four values; tx hash must be 0x + 64 hex), and `validate_trap_set` are all tx-lookup-shaped.
- **`traptest/scoring.py` (`score_answer`):** hardcodes the five tx-lookup fields and their comparisons (status exact case-insensitive; value as Decimal wei; block as int; v2 strict-unknown rule for `not_found`). A new intent needs its own field list and comparison rules — e.g. an integer-equality rule for a count, and its own "unknown" rule.
- **`traptest/normalise.py` (`normalise`):** maps provider field names (`block_number` → `block`, `value_eth` → `value` in wei). A new intent needs its own name mapping and numeric canonicalisation.
- **`traptest/trap_catalog.py` (provenance + composition):** `validate_provenance` enforces tx-lookup category rules (required status per category, unknown-tx must carry status only) and `build_fixed_set` requires ≥1 reverted + ≥1 unknown trap. A new intent needs its own category table and composition rules.
- **`traptest/harness.py` (`load_traps`, `build_scored_row`) and `traptest/leaderboard.py`:** the run/leaderboard pipeline assumes `Trap` objects and `Score` field lists; both work unchanged only if the new scorer still returns the same `Score`/`FieldResult` shapes.
- **Tests:** `tests/test_scoring.py`, `tests/test_traps.py`, `tests/test_trap_catalog.py` and the leaderboard tests encode tx-lookup behaviour; a new intent needs its own test files, and the existing 165 tests must keep passing unchanged (frozen-set scoring is byte-identical by design).

A full assessment of what "config-driven per intent" would take was done during the 13 Nov 2026 growth council and is not included in this kit. Short version: it is a real refactor, not a config tweak, because the tx-lookup shape is baked into five modules plus tests; the safe path is a per-intent scoring config loaded by `score_answer` with the frozen v1 path kept byte-identical, plus a new `Trap`-equivalent per intent.

## Sources

- Trap file envelope + provenance requirements: `traps-frozen-2026-11-06.json`, `traps-frozen-2026-11-09.json`; `traptest/trap_catalog.py` (`validate_provenance`, `build_fixed_set`); `traptest/trap_design.md`.
- Preference-pair format (one JSON object per line, `prompt`/`chosen`/`rejected`): `anjoman-material/preference-pairs.jsonl` (12 lines), `preference-pairs-expansion.jsonl` (12 lines).
- Truth-source YAML shape (miner YAML v1): `anjoman-material/truth-source.yaml`.
- Example ground truth (block 56538934, 4 transactions): verified live against `https://base-sepolia-rpc.publicnode.com` (`eth_getBlockByNumber`) during drafting, 13 Nov 2026; cross-checked by the t13 receipt in the same block (`results-live/expansion-clean-run-2026-11-09.json`, t13 rows).
- $0.01/call, $0.30 default cap, escrow finding, burner funding: `docs/how-to-run.md` §§1–4, §6; `results-live/full-run-2026-11-06.json`; `results-live/expansion-clean-run-2026-11-09.json`.
- Tests 165/165: `python3 -m unittest discover -s tests` (verified 13 Nov 2026; Ran 165, OK).
