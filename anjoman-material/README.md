# Anjoman evaluation material — TrapTest (ONCHAIN_TX_LOOKUP_GENERAL)

SUBMITTED 8 Nov 2026 11:20–11:21 — 12 preference pairs + 1 truth source admitted on
Anjoman (pool went 4 → 5 contributors, activation threshold met). Staged fixes for the
t04/t06/t10 rejected answers are in `review-fixes-2026-11-08/` and are NOT yet re-submitted.
Prepared 8 Nov 2026 from the frozen trap set
(`../traps-frozen-2026-11-06.json`, frozen 6 Nov 2026 13:59:42 UTC — never edited).

Intent: `ONCHAIN_TX_LOOKUP_GENERAL` (class: deterministic, 26 live miners;
canonical request params `tx_hash` + `chain`; response fields `tx_hash`,
`status` [confirmed|reverted|pending|not_found], `from`, `to`,
`block_number`, `value_eth` — per
https://devnode.telegraphprotocol.com/engine/v1/intents/ONCHAIN_TX_LOOKUP_GENERAL).

## Files

| File | What it is |
|---|---|
| `preference-pairs.jsonl` | 12 preference pairs, one per frozen trap (t01–t12, in order). Each line is exactly `{"prompt", "chosen", "rejected"}` — the row shape in the Anjoman docs (`label_kind` defaults to `preference_pair`). |
| `truth-source.yaml` | Miner-YAML-format truth source: the Base Sepolia public JSON-RPC endpoint that the frozen ground truth was itself verified against. |
| `README.md` | This file. |

## Per-trap mapping (preference pairs)

Chosen answers are built strictly from the frozen ground truth (status, from,
to, value, block). For token traps the scored value is the **Transfer-event
amount**, with the native tx value (0 wei) stated alongside so the answer is
unambiguous. Where a trap scores no value (`expected_value: null` in the
frozen file — t05, t06, t07, t09, t10) the chosen answer states no value.

| Trap | Category | Rejected answer — source |
|---|---|---|
| t01 | plain transfer | REAL — TxLens 9002, `results-live/results.json`: answered `not_found` with all fields null for a confirmed tx |
| t02 | plain transfer | REAL — TxLens 9002, same as t01 |
| t03 | token transfer | REAL — TxLens 9002, same as t01 |
| t04 | token transfer | REAL — Truvian 8453, `results-live/results.json`: from/to/block correct, **no status**, value `0` — the native tx value, not the Transfer-event amount (2000000000000000000) |
| t05 | contract interaction | REAL — TxLens 9002, same as t01 |
| t06 | contract interaction | REAL — Truvian 8453: from/to/block/value correct, **no status** (the only defect; missing status is a field failure under strict scoring) |
| t07 | reverted tx | REAL — TxLens 9002, same as t01 (claimed not found for a reverted tx) |
| t08 | reverted tx | REAL — TxLens 9002, same as t01 |
| t09 | multi-recipient | REAL — TxLens 9002, same as t01 |
| t10 | multi-recipient | REAL — Truvian 8453: from/to/block/value correct, **no status** |
| t11 | unknown tx | WRITTEN — no provider gave a wrong answer (TxLens and Truvian both correctly answered `not_found`; Sigil/LiveCert/OnChain Intel returned errors, not answers). Fabricated "confirmed" claim reusing t02's real block/addresses |
| t12 | unknown tx | WRITTEN — same as t11, reusing t01's real block/addresses |

No provider name is invented anywhere: every "REAL" rejected answer is a
faithful rendering of that provider's normalised answer in `results.json`
(same status, same fields, same values). Renderings are prose versions of the
structured answers, not quotes — the run files hold the verbatim records.

Honest nuance, t08: Truvian's live answer for t08 was `value: "1e-05"`
(0.00001 ETH), which is numerically the correct native value
(10000000000000 wei) but failed TrapTest's strict raw-wei string match. It is
**not** used as a rejected answer here; the t08 rejected is TxLens's
`not_found` instead.

## Truth source — format and provenance

Format (authoritative, not guessed):

- Miner YAML v1, following the official truth-source example in
  https://anjoman.ai/docs/scoring/contribute-evaluation-data ("Writing one" —
  the Frankfurter/ECB example) and the full schema in
  https://anjoman.ai/docs/miners/yaml-config.
- The closest GitHub template, issue #87 (`ONCHAIN_METRIC_VERIFY`), says the
  same thing: *"A truth source is a free public API (no key) that gives the
  right answer to the Intent's question. You write it in the same format as a
  miner YAML."* No "miner YAML" format exists in the public
  `telegraphprotocol/bounties` repo (zero mentions of "yaml" in it; the
  closest files are the V2 internal `evaluation-profiles.example.json` /
  `evaluation-state.example.ndjson`, which are a different contract), so the
  Anjoman docs above are the format authority.
- Upload shape (docs): one JSONL row,
  `{"label_kind": "truth_source", "source": "<yaml text>"}`, built with
  `jq -Rsc '{label_kind: "truth_source", source: .}' truth-source.yaml`.
  Verified 8 Nov: that exact command produces a valid row whose embedded YAML
  re-parses (slug `truth-base-sepolia-rpc`).

Content: two POST endpoints against `https://base-sepolia-rpc.publicnode.com`
(free, public, no key — `auth.type: none`):

- `/receipt` — `eth_getTransactionReceipt`. PRIMARY: execution status
  (0x1 confirmed / 0x0 reverted, null = not found), from, to, blockNumber,
  and receipt logs (ERC-20 Transfer events for the token traps).
- `/tx` — `eth_getTransactionByHash`. Supplies the native value (hex wei),
  which a receipt does not carry.

Both declare the four JSON-RPC body params (`jsonrpc`, `method`, `params`
array with the single tx hash, `id`). `input_schema` requires `tx_hash` +
`chain` (`chain` fixed to `base-sepolia` — the RPC URL is chain-specific and
the JSON-RPC methods take no chain argument).

### Assumptions and limits (flagged, not hidden)

1. **JSON-RPC body construction is unverified.** No published docs example
   shows a JSON-RPC POST; all examples are GET/query or simple POST bodies.
   Whether the node's request builder wraps the tx hash into the `params`
   array correctly is unknown. Mitigation: sandbox-validate the YAML at
   `anjoman.ai/dashboard/earn` before submitting — it tests every declared
   endpoint against the real upstream.
2. **Hex/status decoding is the parser's job.** The RPC returns hex values
   and receipt status 0x1/0x0; the node must decode those into
   `block_number` (decimal), `value_eth` (wei → whole units) and the status
   enum. No `intent_mapping` is included, matching the official truth-source
   example (which has none).
3. **Two endpoints, one intent.** The node picks by endpoint description;
   the descriptions steer it to the receipt endpoint first. If the node only
   ever calls one endpoint per question, native value (tx endpoint) and
   status (receipt endpoint) cannot both come from one call.
4. **Duplicate risk.** If another contributor already uploaded this same
   RPC source for this intent, the row is `superseded` as `duplicate_case`
   (same endpoints + parameters = same source, whatever the name/slug).
   Check the pool first:
   `GET /api/evalpool/status?intent_id=ONCHAIN_TX_LOOKUP_GENERAL`.
5. **Deterministic intent, preference pairs secondary.** Per the Season 2
   intents page this intent is deterministic/comparator-only, so the truth
   source is the primary scoring material; the 12 pairs are supplementary
   (they land in the testing half unless the pool treats them otherwise).
   Also note: an intent's questions are only used once its pool holds
   material from **at least 5 different contributors** — TrapTest's 12 pairs
   alone do not activate the intent's question pool (truth sources have no
   such minimum: one is enough to score).

## Verification (run 8 Nov 2026 — all passed)

- `preference-pairs.jsonl`: 12 valid JSON lines; keys exactly
  prompt/chosen/rejected; no empty values; tx hashes match the frozen set
  exactly, in order t01–t12; chosen ≠ rejected; lengths inside the docs'
  limits (prompt 16–16,000 chars; chosen/rejected 8–32,000).
- Every chosen answer cross-checked field by field against the frozen ground
  truth (status, from, to, value where scored, block) — no mismatches.
- Every real rejected answer re-checked against `results.json` normalised
  provider answers — faithful (same status, same fields, same values).
- `truth-source.yaml`: parses; all top-level and endpoint keys inside the
  documented closed sets; `auth.type: none`; `base_url` absolute public
  `https://`; an endpoint lists the intent; 6,317 bytes (< 32 KB), 2
  endpoints (≤ 32).
- Live re-check 8 Nov: the public RPC still answers — `eth_getTransactionByHash`
  for t01 returns from `0xdead…0001`, to `0x4200…0015`, value `0x0`;
  `eth_getTransactionReceipt` for t07 returns status `0x0` (reverted) —
  both matching the frozen ground truth.

Build/verify scripts (kept outside this folder, in /tmp):
`/tmp/build_anjoman.py`, `/tmp/verify_anjoman.py`. Re-run the verifier with
`python3 /tmp/verify_anjoman.py` after any edit. The frozen trap file and all
results files were not modified.

## How to submit (human step — NOT done here)

Per https://anjoman.ai/docs/scoring/contribute-evaluation-data, uploads are
signed (EIP-191 `personal_sign`) and POSTed to the devnode; the Anjoman
dashboard at https://anjoman.ai/dashboard/eval also accepts the files. Do
not upload without Olly's explicit approval; the eval form and the final
submission form are separate steps, and the 1 Dec 23:59 UTC deadline applies
to the submission.
