# TrapTest — competing provider supply re-check (read-only, 28 Oct 2026)

**Method:** free discovery endpoints only — no purchase, no wallet, no
event evidence. This is a snapshot, not a guarantee for the event window.

- Source: `https://devnode.telegraphprotocol.com/engine/v1/intents/ONCHAIN_TX_LOOKUP/miners`
  (fetched 28 Oct 2026, ~10:09 UTC) and the intents catalogue
  `https://devnode.telegraphprotocol.com/engine/v1/intents`.
- Intents catalogue: **134 canonical intents** (`count: 134`), unchanged
  from the 27 Oct check.

## Counts — ONCHAIN_TX_LOOKUP, 28 Oct 2026

| Measure | Count |
|---|---|
| Miners listed for the intent | **23** (same total as 27 Oct) |
| Blockscout list-only endpoints (recent-txs / blocks / token-transfer
  lists, not tx-hash lookups) | **10** |
| Non-Blockscout miners | **13** |
| Of those, describing a tx-hash lookup in their catalogue description | **12** |
| Excluded from the usable-looking count | VulnFeed — its description is
  contract-security analysis from a contract address, not a
  transaction-hash lookup; treat as unproven for this intent until a
  live probe says otherwise |

Usable-looking providers (by description, **not** by live probe — names
only, no IDs recorded here, because IDs are not stable):

INTERLOCK On-Chain Transaction Lookup, Veyctum Transaction Effect
Oracle, Truvian Exact On-Chain Truth Engine, Verity On-Chain
Transaction Lookup, Sigil Multi-Chain Transaction Lookup, ChainWire
Transaction Lookup, TxLens, ChainSight On-Chain Intelligence Hub,
DegenLens On-Chain Intelligence, OnChain Intel Miner, LiveCert Sourced
Answers, PREFLIGHT Infrastructure Signals.

## What this does and does not establish

- **Establishes:** competing supply is still listed at the same level
  as the 27 Oct check (23 listed, 12 usable-looking by description).
  The ≥2-provider minimum for a leaderboard is still plausible on
  catalogue evidence alone.
- **Does NOT establish:** that any named provider will actually answer
  a tx-hash Direct Ask in the event window, at what 402 price, or with
  what answer schema. Catalogue presence is not a live probe. The
  day-1 pre-flight (cheap probe of ≥2–3 tx-capable providers before
  freezing the trap set) is still required, and a provider that does
  not answer must not be presented as scored.
- **Warning — miner IDs are not stable:** do not copy IDs from any
  re-check into code, docs, or the submission. The live client
  re-fetches the catalogue at run time for every buy and refuses to
  buy from an ID absent from the fresh list.
- **Price warning:** every listed miner shows `cost_per_call: "0.00"`
  in the catalogue. That field is never a price. Real prices come
  only from the live 402 challenge at purchase time.
