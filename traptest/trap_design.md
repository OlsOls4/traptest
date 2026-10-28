# TrapTest — trap set design (prep, 27 Oct 2026)

**Status: PREP ONLY.** This document and `trap_catalog.py` define the
_structure_ of the fixed trap set. They contain **no real transaction
hashes, no live Telegraph purchases, no hardcoded miner IDs, and no
event evidence**. Real traps are populated in the event window
(1 Nov–1 Dec 2026) by checking each candidate transaction against a
public Base Sepolia explorer/API, recording provenance, and freezing
the set before the first provider is scored. Mock fixtures in tests
are framework tests only and must never be submitted as results.

Intent: `ONCHAIN_TX_LOOKUP` only. Chain: Base Sepolia (84532).
Miner IDs are re-fetched at run time (`providers.py`) — never hardcoded.

## 1. The fixed-set rule

A trap is a query whose ground truth is known **in advance** and
**independent of any provider's answer**. The set is frozen before
scoring begins and is never tuned afterwards — not to flatter a
provider, and not to punish one either. If a trap's ground truth
turns out to be wrong, the honest move is to disclose and retire
that trap, not to quietly re-score it. (Exception with its own rule:
`unknown_tx`, §3.)

Scoring itself is unchanged from `scoring.py`: status must match
exactly; a missing provider field is a failure, never a pass; overall
pass requires status plus every scored field.

## 2. Categories and required ground-truth fields

The Trap schema scores only `status, from, to, value, block`. A
category is therefore scored only on the fields below; anything else
about the transaction is a note, not a score. "Required" means the
trap must carry that field or `build_fixed_set` rejects the set.

| Category | Required GT fields | Optional | What it catches |
|---|---|---|---|
| `plain_transfer` — native ETH transfer, confirmed | status=confirmed, from, to, value, block | — | Wrong sender/recipient/amount/block |
| `token_transfer` — ERC-20 transfer, confirmed | status=confirmed, from, to, value, block | — | Reporting the tx value field (0) instead of the Transfer event amount; misread event logs |
| `contract_interaction` — confirmed call with non-empty input data | status=confirmed, from, to (contract), block | value, only if the tx value is non-zero and unambiguous | Failing on contract calls; reporting a log address as the tx recipient |
| `reverted_tx` — receipt status 0 **(mandatory)** | status=reverted, from, to, block | value, only if unambiguous | Reporting reverted transactions as confirmed — the cheapest provider failure, and the one most worth catching |
| `multi_recipient_tx` — one tx, multiple recipients (multisend/batch) | status=confirmed, from, to, block | value (tx-level only, if unambiguous) | Conflating a log recipient with the tx recipient; failing on batched txs. **Limitation:** the recipient list is recorded in notes but NOT scored — the schema has no list field, so omitting recipients is not a failure here |
| `unknown_tx` — well-formed hash with no explorer record at freeze time **(mandatory)** | status=not_found only | — (from/to/value/block must ALL be None) | Hallucinating details for a transaction that does not exist |

### Value-basis rule (the trap that would otherwise be unfair)

`value` means different things for different categories, and a trap
that does not say which one it means is not a fair test:

- `plain_transfer`: tx value field, raw wei as a string.
- `token_transfer`: Transfer **event** amount in raw token units. The
  trap record must name the token contract and state that the value
  is the event amount — a provider returning the tx value field (0)
  is then scored wrong, correctly, not as a convention difference.
- `contract_interaction`, `reverted_tx`, `multi_recipient_tx`: value
  is scored only when the tx value field is non-zero and
  unambiguous; otherwise it is left `None` (unscored). Contract
  calls' meaningful amounts live in logs, which this schema does not
  score — that is a known limitation, not a reason to guess a value.

### Recommended composition (default set: 12 traps)

3 plain_transfer, 3 token_transfer, 2 contract_interaction,
2 reverted_tx, 1 multi_recipient_tx, 1 unknown_tx.
`RECOMMENDED_COMPOSITION` in `trap_catalog.py` encodes this.
Every set, whatever its size, must contain at least one
`reverted_tx` and one `unknown_tx` — enforced by `build_fixed_set`.

## 3. Provenance: how ground truth is checked

Every real trap carries a `GroundTruthProvenance`:

- `source_name` — e.g. "BaseScan Sepolia".
- `source_url` — full http(s) URL of the explorer/API record checked
  (transaction page, receipt, or event-log view).
- `tx_reference` — must equal the trap's `tx_hash` exactly.
- `block_reference` — must equal `expected_block` when the trap has one.
- `checked_at` — ISO date of the check; `checker` — who/what checked.
- `notes` — value basis, token contract, recipient list, anything
  a reviewer needs to reproduce the check.

`validate_provenance` rejects: a provenance/trap id mismatch, an
unknown category, a non-`ONCHAIN_TX_LOOKUP` intent, a status that
does not match the category's required status, a missing required
field, an `unknown_tx` carrying any field beyond status, a
non-http(s) or empty source URL, a tx/block reference mismatch, or
missing `checked_at`/`checker`. `pending` is rejected outright (see §5).

### Freeze procedure (event window, from 1 Nov)

1. Pick candidate transactions from the public explorer (BaseScan
   Sepolia or equivalent public API) — real, already-mined txs for
   the five mined categories; a searched-and-absent hash for
   `unknown_tx`.
2. For each, record the provenance above, with the source URL and
   block/tx reference, and have the check repeated (second pair of
   eyes or a second source) before freezing.
3. Freeze the set (write it as data, not code changes to categories)
   and record the freeze date. Run providers only after freezing.
4. If a trap is later found wrong: retire it and disclose the
   retirement; do not re-score it. For `unknown_tx` specifically:
   if the hash later appears on chain, retire the trap — never
   re-score it against the new record, because its test was
   "what do you say about a transaction that does not exist".

## 4. Size and cost cap

- Recommended: 12 traps × 2 providers = 24 served calls.
- Hard cap: 30 traps (`MAX_TRAPS`), i.e. 60 calls at 2 providers.
- At the docs' ~$0.01/call in testnet USDC plus the 2% protocol fee:
  12 traps × 2 providers ≈ $0.24 + $0.0048 ≈ **$0.245**; the 30-trap
  cap ≈ $0.60 + $0.012 ≈ **$0.612**. These are planning estimates
  from the docs figure, not a measured bill — real prices come from
  the live 402 challenge at run time. `estimate_cost()` computes this.
- Cost is not the reason for the cap alone: a trap set's value is
  that every trap is hand-checked. Past ~30, checking quality, not
  money, is what degrades first.

## 5. Categories rejected, and why

- **`pending_tx` (a transaction still in the mempool).** Ground truth
  is not fixed: a pending transaction confirms (or drops) and its
  truth changes after the trap is written. That breaks the fixed-set
  rule itself, so pending traps are rejected by validation, not
  merely discouraged.
- **USD-value traps ("was this transfer worth $X?").** Prices move;
  the ground truth would be true only at a moment in time. Only raw
  native/token amounts are fixed and therefore trappable.
- **Gas-fee traps.** Fee reporting conventions vary (gas used × gas
  price, effective price, different units) and the Trap schema has
  no fee field. Scoring a provider on an unscored, convention-laden
  field would be unfair, not rigorous.
- **Internal-transfer / trace-detail traps (e.g. "list every internal
  transfer", MEV/sandwich detail).** The discriminating detail needs
  trace decoding and a list-valued answer; the schema scores single
  from/to/value only. Kept out until the schema grows a list field —
  `multi_recipient_tx` is the honest tx-level version of this idea.
- **Cross-chain / bridged-transaction traps.** A Base Sepolia lookup
  alone cannot establish the destination-chain outcome, so no
  single public record settles the ground truth.
- **Private / mempool-only transactions.** Not checkable against a
  public explorer at all; ground truth would rest on the trap
  author's word, which is exactly what TrapTest exists to avoid.
- **Self-transfer as its own category.** Checkable (from == to) but
  adds nothing a plain transfer does not already test; folded in as
  a possible plain_transfer variant, not a separate category.

## 6. Known limitations (stated, not hidden)

- Per-recipient amounts and recipient lists are notes, not scores
  (`multi_recipient_tx`).
- Contract-call amounts inside logs are not scored
  (`contract_interaction`).
- Provider answers in different units/conventions (e.g. ETH vs wei)
  are compared as strings after lowercasing by `scoring.py`; the
  run harness must normalise provider output to the trap's stated
  value basis before scoring, or unit differences will read as
  failures. That normalisation belongs in the run harness (event
  window), not in the trap definitions.
- `unknown_tx` traps have a shelf life: they are valid only while
  the hash stays absent from the chain (see retirement rule, §3).
- This catalogue covers `ONCHAIN_TX_LOOKUP` only. A second trap
  intent (e.g. transfer verification) would need its own category
  table and provenance rules — it is not smuggled in here.

## 7. Files

- `traptest/trap_catalog.py` — `CATEGORY_SPECS`,
  `GroundTruthProvenance`, `validate_provenance`,
  `estimate_cost`, `build_fixed_set`, size/cost constants.
- `tests/test_trap_catalog.py` — mock fixtures only; covers
  provenance mismatches, mandatory categories, size cap, and cost
  maths. Not event evidence.
