# Anjoman evaluation material — TrapTest (ONCHAIN_TX_LOOKUP_GENERAL)

**STAGED CORRECTION — review-fixes-2026-11-08.** This is the corrected README
to accompany `preference-pairs.fixed.jsonl`. It is staged in
`review-fixes-2026-11-08/` and is **not** the live file: the live files in
`anjoman-material/` were **not touched** because a submission of them was in
flight on anjoman.ai when this review ran (8 Nov 2026). See
`fixes-2026-11-08.md` in the same staging folder for the apply instructions.

The live README's header ("PREP ONLY. Nothing here has been submitted") is
**stale as of this review** — a browser-task worker was submitting this
material on anjoman.ai at the time of writing. Do not rely on the live
README's submission status; check the Anjoman dashboard instead.

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
| `preference-pairs.jsonl` | 12 preference pairs, one per frozen trap (t01–t12, in order). Each line is exactly `{"prompt", "chosen", "rejected"}` — the row shape in the Anjoman docs (`label_kind` defaults to `preference_pair`). **Live file: 3 of its rejected answers are weak/ambiguous — see "Changes in the fixed file" below. Use `review-fixes-2026-11-08/preference-pairs.fixed.jsonl` instead once the in-flight submission completes.** |
| `truth-source.yaml` | Miner-YAML-format truth source: the Base Sepolia public JSON-RPC endpoint that the frozen ground truth was itself verified against. **Validation status: UNVALIDATED — the sandbox validator has not been run. See "Truth source — validation status" below. Do not claim otherwise.** |
| `README.md` | This file (live copy). The corrected copy is `review-fixes-2026-11-08/README.fixed.md`. |

## Per-trap mapping (preference pairs)

Chosen answers are built strictly from the frozen ground truth (status, from,
to, value, block). For token traps the scored value is the **Transfer-event
amount**, with the native tx value (0 wei) stated alongside so the answer is
unambiguous. Where a trap scores no value (`expected_value: null` in the
frozen file — t05, t06, t07, t09, t10) the chosen answer states no value.

**Provenance — every pair, verified 8 Nov 2026 against
`../traps-frozen-2026-11-06.json` and
`../results-live/full-run-2026-11-06.json` (60 rows; identical content in
`../results-live/results.json`).** "REAL" = a faithful prose rendering of
that provider's normalised answer in the run file (same status, same fields,
same values). "CONSTRUCTED" = no provider ever gave this answer; it was
written for the pair and is labelled as such here because the JSONL schema
(`prompt`/`chosen`/`rejected` only — no extra keys allowed) cannot carry a
provenance flag. A consumer of the JSONL alone cannot tell REAL from
CONSTRUCTED; this README is the only provenance record.

| Trap | Category | Chosen source | Rejected source |
|---|---|---|---|
| t01 | plain transfer | Frozen ground truth: confirmed, `0xdead…0001` → `0x4200…0015`, value 0 wei, block 53047427 | REAL — TxLens 9002, full-run: `not_found`, all fields null, for a confirmed tx |
| t02 | plain transfer | Frozen ground truth: confirmed, `0xb0b8…ad7` → `0xb0b8…ad7`, value 1000000000000000 wei, block 55258439 | REAL — TxLens 9002, full-run: `not_found`, all fields null |
| t03 | token transfer | Frozen ground truth: confirmed, `0x0af9…bd5` → `0x2736…d047`, Transfer amount 950000, native 0 wei, block 53047427 | REAL — TxLens 9002, full-run: `not_found`, all fields null |
| t04 | token transfer | Frozen ground truth: confirmed, `0x2735…348` → `0x8247…12d8`, Transfer amount 2000000000000000000, native 0 wei, block 55258552 | **FIXED — see below.** Live file: REAL — Truvian 8453, full-run: no status, from/to/block correct, value `0` (the native tx value, not the scored Transfer amount). Fixed file: CONSTRUCTED counterfactual — wrong status, wrong amount, wrong block |
| t05 | contract interaction | Frozen ground truth: confirmed, `0xdead…0001` → `0x4200…0015` (contract), block 55258576, no value scored | REAL — TxLens 9002, full-run: `not_found`, all fields null |
| t06 | contract interaction | Frozen ground truth: confirmed, `0xdead…0001` → `0x4200…0030` (contract), block 55258576, no value scored | **FIXED — see below.** Live file: REAL — Truvian 8453, full-run: no status, from/to/block/value all correct. Fixed file: CONSTRUCTED counterfactual — wrong status, wrong recipient, wrong block |
| t07 | reverted tx | Frozen ground truth: reverted, `0xe498…d8f` → `0x572b…76b`, block 55258569, no value scored | REAL — TxLens 9002, full-run: `not_found`, all fields null, for a reverted tx |
| t08 | reverted tx | Frozen ground truth: reverted, `0x40dd…903` → `0x94cc…bc4`, value 10000000000000 wei, block 55258555 | REAL — TxLens 9002, full-run: `not_found`, all fields null |
| t09 | multi-recipient | Frozen ground truth: confirmed, `0x0de5…205` → first recipient `0x8416…48d`, 2 Transfer events, block 55258574 | REAL — TxLens 9002, full-run: `not_found`, all fields null |
| t10 | multi-recipient | Frozen ground truth: confirmed, `0x0dec…604` → first recipient `0x8416…48d`, 2 Transfer events, block 55258573 | **FIXED — see below.** Live file: REAL — Truvian 8453, full-run: no status, from/to/block/value all correct. Fixed file: CONSTRUCTED counterfactual — wrong status, wrong Transfer count, wrong block |
| t11 | unknown tx | Frozen ground truth: `not_found`, no sender/recipient/value/block | CONSTRUCTED counterfactual — "confirmed" in block 55258439, `0xb0b8…ad7` → `0xb0b8…ad7`, value 1000000000000000 wei (t02's real ground truth, reused). No provider gave a wrong answer: TxLens 9002 and Truvian 8453 both correctly answered `not_found` (both scored PASS); LiveCert 4433 / Sigil 9010 / OnChain Intel 900 returned errors, not answers |
| t12 | unknown tx | Frozen ground truth: `not_found`, no sender/recipient/value/block | CONSTRUCTED counterfactual — "confirmed" in block 53047427, `0xdead…0001` → `0x4200…0015`, value 0 wei (t01's real ground truth, reused). Same as t11: both answering providers correctly said `not_found`; the rest errored |

No provider name is invented anywhere: every "REAL" rejected answer is a
faithful rendering of that provider's normalised answer in the run file
(same status, same fields, same values). Renderings are prose versions of the
structured answers, not quotes — the run files hold the verbatim records.

Honest nuance, t08: Truvian's live answer for t08 was `value: "1e-05"`
(0.00001 ETH), which is numerically the correct native value
(10000000000000 wei) but failed TrapTest's strict raw-wei string match. It is
**not** used as a rejected answer here; the t08 rejected is TxLens's
`not_found` instead.

## Changes in the fixed file (review 8 Nov 2026)

Three rejected answers in the live `preference-pairs.jsonl` are weak or
ambiguous training signals. All three are replaced in
`preference-pairs.fixed.jsonl` with clearly-wrong, still-plausible
provider-style answers. **No prompt and no chosen answer changed** — all 12
chosen answers were verified field-by-field against the frozen ground truth
and all 12 are correct (see `fixes-2026-11-08.md` for the verification
output). Full before/after text for each changed pair is in that file.

- **t06 and t10 — near-correct rejected answers.** The live rejected answers
  render Truvian 8453's real answers: correct sender, recipient, block and
  value 0 on every stated field, differing from the chosen only by omitting
  the word "confirmed"/status. Worse than the live README said: for both
  traps `expected_value` is `null` (unscored), so the stated "value 0" is
  the factually correct native tx value — the rejected is correct on
  **every stated field** and its only defect is a missing status word. A
  judge reading the pair could reasonably call the rejected correct. Fixed
  rejected answers state the wrong status (`reverted` instead of
  `confirmed`) plus a wrong recipient/block (t06) or wrong Transfer count
  and block (t10) — wrong on three scored fields each.
- **t04 — defensible alternative reading.** The live rejected renders
  Truvian 8453's real answer: correct from/to/block and "value 0". That 0
  is the true native tx value; the scored value is the Transfer-event amount
  (2000000000000000000). "Value 0" is therefore a defensible reading of the
  prompt's "value" wording, not a hallucination — a noisy pair. The fixed
  rejected states the wrong status (`reverted`), a wrong token amount
  (1000000000000000000 instead of 2000000000000000000) and a wrong block
  (55258553 instead of 55258552) — wrong under either value reading.
- **t11 and t12 — kept as constructed counterfactuals.** The live rejected
  answers were written, not observed: both providers that answered said
  `not_found` correctly. But the constructed claims are **clearly wrong**
  (they assert "confirmed" with another trap's real block/addresses for a
  hash whose ground truth is `not_found` with no fields), so they are kept
  unchanged and are labelled CONSTRUCTED in the table above. If a future
  reviewer judges a constructed counterfactual unacceptable in principle,
  the honest replacement is a provider error, not a fabricated answer —
  but no provider gave a wrong answer for these traps, so there is no
  observed wrong answer to substitute.

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

### Truth source — validation status: UNVALIDATED

**The truth source has not been validated. Do not claim otherwise.** The YAML
itself flags this in its Known Limits §§2–3, and this review confirms no
validation is recorded anywhere in the folder:

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

What was checked in this review (8 Nov, no browser — the sandbox validator
could not be run from here): `truth-source.yaml` parses cleanly; all
top-level and endpoint keys are inside the documented closed sets;
`auth.type: none`; `base_url` is absolute public `https://` and **matches
the frozen ground truth's own provenance URL exactly**
(`https://base-sepolia-rpc.publicnode.com`, per
`traps-frozen-2026-11-06.json`); both endpoints declare the correct
JSON-RPC methods (`eth_getTransactionReceipt`, `eth_getTransactionByHash`)
with the four body params (`jsonrpc`/`method`/`params` array/`id`); intent
name `ONCHAIN_TX_LOOKUP_GENERAL` is correct in endpoints and semantics;
`input_schema` requires `tx_hash` + `chain` (`base-sepolia` only);
`output_schema` status enum is exactly
`[confirmed, reverted, pending, not_found]`; 6,317 bytes (< 32 KB),
2 endpoints (≤ 32). **No factual error was found in the YAML, so no
`truth-source.fixed.yaml` was staged** — the remaining step is validation,
not correction.

To validate (human/browser step): open `anjoman.ai/dashboard/earn`, run the
sandbox validator on `truth-source.yaml`, and confirm (a) both endpoints
return live data for a known hash (e.g. t01
`0xd47a090fee50ae43d3af7dcb03eced0be6c98a48b3aa92dc21a8c4d9d784ae96`),
(b) the `params` array is built with exactly the one tx hash, and (c) the
response parser decodes hex value/blockNumber and receipt status 0x1/0x0
into the intent's answer format. Record the result here before relying on
the source.

## Verification (run 8 Nov 2026)

Original build verification (all passed at build time):

- `preference-pairs.jsonl`: 12 valid JSON lines; keys exactly
  prompt/chosen/rejected; no empty values; tx hashes match the frozen set
  exactly, in order t01–t12; chosen ≠ rejected; lengths inside the docs'
  limits (prompt 16–16,000 chars; chosen/rejected 8–32,000).
- Every chosen answer cross-checked field by field against the frozen ground
  truth (status, from, to, value where scored, block) — no mismatches.
- Every real rejected answer re-checked against the run file's normalised
  provider answers — faithful (same status, same fields, same values).
- `truth-source.yaml`: parses; all top-level and endpoint keys inside the
  documented closed sets; `auth.type: none`; `base_url` absolute public
  `https://`; an endpoint lists the intent; 6,317 bytes (< 32 KB), 2
  endpoints (≤ 32).
- Live re-check 8 Nov: the public RPC still answers — `eth_getTransactionByHash`
  for t01 returns from `0xdead…0001`, to `0x4200…0015`, value `0x0`;
  `eth_getTransactionReceipt` for t07 returns status `0x0` (reverted) —
  both matching the frozen ground truth.

Review verification, 8 Nov 2026 (this staging round — scripts in /tmp:
`/tmp/verify_review.py`, `/tmp/validate_fixed.py`; build script
`/tmp/build_fixed.py`):

- Re-verified all 12 live chosen answers against the frozen ground truth
  programmatically (status, from, to, block, scored value): **12/12 correct.
  No chosen answer changed.**
- Re-verified every live rejected answer against the run file's normalised
  provider answers: the 7 TxLens `not_found` renderings and the 3 Truvian
  renderings (t04/t06/t10) are all faithful; t11/t12 confirmed constructed
  (both answering providers said `not_found` correctly; the other three
  errored). Panel findings F1 (constructed t11/t12, no provenance in the
  JSONL itself), F2 (t06/t10 near-correct) and F3 (t04 defensible "value 0")
  **all confirmed** — with F2 stronger than stated (t06/t10 rejected are
  correct on every stated field, value 0 being the true native value for
  unscored traps) and F1 qualified (the live README *does* label t11/t12
  WRITTEN; the gap is that the JSONL rows themselves carry no provenance).
- Validated `preference-pairs.fixed.jsonl` programmatically: 12 valid JSON
  lines; keys exactly prompt/chosen/rejected; no empty values; tx hashes
  match the frozen set exactly, in order t01–t12; prompts and chosen answers
  byte-identical to the live file; exactly 3 rejected answers changed
  (t04/t06/t10); **every chosen answer correct and every rejected answer
  clearly wrong** (each rejected contradicts the frozen ground truth on at
  least one scored field — status, address, block, token amount or Transfer
  count — verified per row; see `fixes-2026-11-08.md`).
- `truth-source.yaml`: re-parsed and fact-checked (above) — no factual
  error found; validation status remains UNVALIDATED (sandbox validator not
  run — no browser in this review).
- Live files untouched: sha256 of `preference-pairs.jsonl`,
  `truth-source.yaml` and `README.md` verified identical before and after
  this review.

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

**If the in-flight submission already uploaded the live (unfixed) files,
apply the staged fixes and re-submit** — see `fixes-2026-11-08.md` for the
exact steps.
