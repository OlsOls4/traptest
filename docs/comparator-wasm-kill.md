# Comparator WASM — KILLED with evidence (9 Nov 2026)

**Decision: DO NOT BUILD.** A Telegraph comparator WASM for TrapTest's intent
was investigated, fully specified from the official docs, and killed on three
independent grounds. Do not revisit unless **both** conditions hold: platform
bug #171 is fixed **and** Sireadell's registration 118 goes active.

## What a comparator would have to be (verified from official docs)

- WASM module exporting `imw_score_deterministic`, `imw_alloc`, `imw_free`.
- Constraints: ≤32 MB, `wasm32-unknown-unknown` target, no WASI, zero imports.
- Registration via `registerWasm` on the Diamond contract
  `0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b`, with a $5 MACHINA bond + gas.
- Needs a hosted runnable endpoint (the comparator must be served somewhere
  the platform can call it).

## Why it was killed

### (a) A comparator scores ONE integer only — TrapTest's scoring cannot be expressed

For intent `ONCHAIN_TX_LOOKUP_GENERAL`, only `block_number` is
`"scored": true`. The other scored fields — `value_eth`, `status`, `from`,
`to` — are **not** scored by the platform. TrapTest's scoring is multi-field
and strict (status mismatch fails outright, a missing field is a failure, an
invented field on an unknown tx fails outright). A single-integer comparator
cannot express that. Building one would score a fraction of what TrapTest
scores and misrepresent the rest as unscored.

### (b) Zero differentiation — the intent is already scored by a generic fallback

The platform already scores this intent with a generic fallback implementing
the same rule the comparator would implement (block-number comparison). A
TrapTest comparator would duplicate that fallback exactly and change no
provider's score. There is no scoring gap for a custom comparator to fill.

### (c) Activation is blocked by known unfixed platform bug #171

Comparators sit in `awaiting_compatible_material` forever: the family prefix
`ONCHAIN_TX_LOOKUP` carries class `judgment` while the child intent is
`deterministic`, so no comparator can ever become compatible with material
for this intent family. Until #171 is fixed, a registered comparator cannot
activate at all — the $5 MACHINA bond + gas would buy a permanently pending
registration.

## Correction to the 8 Nov recon

The 8 Nov recon reported no comparator in flight for this intent. That was
wrong. A comparator **does** exist in-flight:

- **Sireadell** (Season 1 Track 1 winner, author of TxLens) — registration
  **118**, pending since 3 Nov 2026. Still pending at kill time (9 Nov 2026),
  consistent with bug #171 blocking activation.
- **zkasuran** — registration 84, deregistered after ~17h.

Sireadell's pending registration does not change the kill: one integer,
zero differentiation, and #171 still blocks activation. It is the signal to
watch — if #171 is fixed **and** reg 118 goes active, the comparator route
may be worth re-examining.

## Sources

- Official comparator format/registration docs (exports, size/target/WASI/
  import constraints, `registerWasm`, Diamond address, $5 MACHINA bond).
- Platform bug #171 (family-prefix class mismatch, `awaiting_compatible_material`).
- Registration records: Sireadell reg 118 (pending since 3 Nov 2026);
  zkasuran reg 84 (deregistered after ~17h).
- Research 9 Nov 2026; decision recorded here so a judge can verify the kill
  without taking it on trust. No comparator was built, registered, or bonded;
  zero spend.
