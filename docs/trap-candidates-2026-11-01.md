# Trap candidates — work-in-progress, NOT the freeze (1 Nov 2026)

These are candidate trap transactions pulled live from Base Sepolia for
the TrapTest trap set. They are NOT yet the frozen set: the freeze
happens immediately before the first scored purchase, once the accepted
test token (0xcc19… on Sepolia) is funded, and every frozen trap gets
full provenance (source URL, block, checker, checked-at) at freeze time.

- Confirmed plain transfer candidate: tx
  0xd47a090fee50ae43d3af7dcb03eced0be6c98a48b3aa92dc21a8c4d9d784ae96,
  block 53047427, receipt status 0x1.
- Token-transfer candidate (Transfer event in receipt logs): tx
  0x0113bafdf54755989384d25240447e2071e4888da16686d180cc4eacc846b9af,
  block 53047427, receipt status 0x1.

Still needed at freeze: a reverted-tx trap (receipt status 0x0, mandatory),
an unknown-tx trap (a well-formed hash with no chain record, mandatory),
plus contract-interaction and multi-recipient cases, to reach the
recommended 12 traps × 2 providers. No purchase has been made; no trap
here has been scored.

**Update 6 Nov 2026:** purchases HAVE now been made — 12 frozen traps ×
5 providers, 60 scored rows in `results-live/full-run-2026-11-06.json`
(Truvian 3/12, TxLens 2/12, LiveCert/Sigil/OnChain Intel 0/12 served 0).
The candidates above were pre-freeze working notes, not the frozen set;
the frozen set is `traps-frozen-2026-11-06.json` (frozen 13:59 UTC).
