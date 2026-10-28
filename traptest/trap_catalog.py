"""Fixed trap-set catalogue design for ONCHAIN_TX_LOOKUP.

PREP ONLY (before 1 Nov 2026): this module defines the STRUCTURE of the
fixed trap set — categories, required ground-truth fields, provenance
rules, and size/cost caps. It contains NO real transaction hashes, NO
live Telegraph purchases, NO hardcoded miner IDs, and NO event evidence.
Real traps are populated in the event window (1 Nov–1 Dec 2026) by
checking each candidate transaction against a public Base Sepolia
explorer/API and recording the provenance (see GroundTruthProvenance).
A trap set is FROZEN before the first provider is scored and is never
retuned to flatter (or punish) a provider afterwards.

Design constraints inherited from the scaffold:
- Scoring (traptest/scoring.py) scores only the fields present on Trap:
  status, from, to, value, block. A category whose discriminating detail
  lives outside those fields cannot be scored on that detail — it is
  either kept with its limitation stated, or rejected (see trap_design.md).
- Miner IDs are re-fetched at run time (traptest/providers.py) — never
  hardcoded here or anywhere else.
- Cost cap: ~$0.01 per served call in testnet USDC (docs figure) plus
  the 2% protocol fee, times traps x providers. The set stays in the
  order of tens of traps x 2 providers.
"""
from dataclasses import dataclass

from .traps import Trap, validate_trap_set

INTENT = "ONCHAIN_TX_LOOKUP"
CHAIN = "Base Sepolia (chain ID 84532)"

# --- Size / cost caps -------------------------------------------------
RECOMMENDED_TRAP_COUNT = 12
MAX_TRAPS = 30  # hard cap: a larger set buys breadth, not trust
PROVIDERS_PER_TRAP = 2
COST_PER_CALL_USD = 0.01  # docs figure for a typical call, testnet USDC
PROTOCOL_FEE_RATE = 0.02
EVENT_WINDOW_START = "2026-11-01"
EVENT_WINDOW_END = "2026-12-01"

# --- Categories --------------------------------------------------------
# scored_fields: Trap fields this category is scored on. A field listed
# under optional_fields may be set on a trap only when its value is
# unambiguous from the public record (see value_basis); otherwise it
# must be left None (unscored), never guessed.
CATEGORY_SPECS = {
    "plain_transfer": {
        "description": "Native ETH transfer, confirmed, single recipient.",
        "scored_fields": ("status", "from", "to", "value", "block"),
        "required_fields": ("status", "from", "to", "value", "block"),
        "optional_fields": (),
        "required_status": "confirmed",
        "value_basis": "Transaction value field, raw wei as a string, "
                       "exactly as the public record reports it.",
        "ground_truth_source": "Explorer transaction page + receipt "
                               "(status 1, from, to, value, block number).",
        "catches": "Providers that misread sender, recipient or amount, "
                   "or report the wrong block.",
    },
    "token_transfer": {
        "description": "ERC-20 token transfer, confirmed. Scored on the "
                       "Transfer event, NOT on the transaction value field "
                       "(which is 0 for a token transfer).",
        "scored_fields": ("status", "from", "to", "value", "block"),
        "required_fields": ("status", "from", "to", "value", "block"),
        "optional_fields": (),
        "required_status": "confirmed",
        "value_basis": "Transfer event amount in the token's raw units, "
                       "as decoded from the event log. The trap record "
                       "must state the token contract and that the value "
                       "is the event amount, so a provider returning the "
                       "tx value field (0) is scored as wrong, not as a "
                       "convention difference.",
        "ground_truth_source": "Explorer transaction page: receipt status, "
                               "Transfer event log (from, to, amount), "
                               "block number.",
        "catches": "Providers that report the tx value field (0) for a "
                   "token transfer, or that miss/misread the event log.",
    },
    "contract_interaction": {
        "description": "Confirmed transaction calling a contract (e.g. a "
                       "swap, mint or approval) with non-empty input data.",
        "scored_fields": ("status", "from", "to", "block"),
        "required_fields": ("status", "from", "to", "block"),
        "optional_fields": ("value",),
        "required_status": "confirmed",
        "value_basis": "Set value ONLY if the transaction value is "
                       "non-zero and unambiguous; otherwise leave it "
                       "None. A contract call's meaningful amounts live "
                       "in its logs, which this schema does not score.",
        "ground_truth_source": "Explorer transaction page: receipt status, "
                               "from, to (contract address), block number; "
                               "input data non-empty.",
        "catches": "Providers that fail on contract calls (e.g. "
                   "reporting no recipient, or a decoded-log address as "
                   "the tx recipient).",
    },
    "reverted_tx": {
        "description": "Transaction whose receipt status is 0 (reverted). "
                       "The single most discriminating category: a "
                       "provider that reports it as confirmed fails "
                       "outright on status.",
        "scored_fields": ("status", "from", "to", "block"),
        "required_fields": ("status", "from", "to", "block"),
        "optional_fields": ("value",),
        "required_status": "reverted",
        "value_basis": "Set value ONLY if the transaction value field is "
                       "unambiguous; reverted calls' meaningful amounts "
                       "are not reliably recoverable, so value defaults "
                       "to unscored.",
        "ground_truth_source": "Explorer transaction page: receipt status 0, "
                               "from, to, block number.",
        "catches": "Providers that ignore receipt status and report "
                   "every mined transaction as confirmed.",
    },
    "multi_recipient_tx": {
        "description": "One confirmed transaction that moves value to "
                       "multiple recipients (e.g. a multisend/batch). "
                       "LIMITATION: the Trap schema scores single from / "
                       "to / value only, so this category is scored on "
                       "tx-level fields alone. The recipient list itself "
                       "is recorded in notes but NOT scored — a provider "
                       "that reports one recipient is not failed for "
                       "omitting the others.",
        "scored_fields": ("status", "from", "to", "block"),
        "required_fields": ("status", "from", "to", "block"),
        "optional_fields": ("value",),
        "required_status": "confirmed",
        "value_basis": "Tx-level value field only, set only if "
                       "unambiguous; per-recipient amounts are notes, "
                       "not scored fields.",
        "ground_truth_source": "Explorer transaction page + event logs "
                               "showing more than one recipient; tx-level "
                               "from, to, block from the tx page.",
        "catches": "Providers that conflate a log recipient with the "
                   "tx recipient, or that fail on batched transactions. "
                   "Does NOT catch recipient-list omissions (see "
                   "limitation).",
    },
    "unknown_tx": {
        "description": "A well-formed 0x hash with NO record on the public "
                       "explorer at freeze time. Tests hallucination: a "
                       "provider inventing sender/recipient/amount for a "
                       "transaction that does not exist fails.",
        "scored_fields": ("status",),
        "required_fields": ("status",),
        "optional_fields": (),
        "required_status": "not_found",
        "value_basis": "None — no value exists. from, to, value and "
                       "block must ALL be None, so any invented field "
                       "is a field failure.",
        "ground_truth_source": "Explorer search for the hash returning no "
                               "record, recorded at freeze time (source "
                               "URL + the searched hash). RETIREMENT RULE: "
                               "if the hash later appears on chain, the "
                               "trap is retired (removed from scoring), "
                               "never re-scored against the new record.",
        "catches": "Providers that hallucinate details for unknown "
                   "transactions instead of reporting not_found.",
    },
}

# A fixed set that cannot catch the two cheapest provider failures —
# ignoring reverts and hallucinating unknown transactions — is not a
# trap set. Both categories are therefore mandatory in every set.
MANDATORY_CATEGORIES = ("reverted_tx", "unknown_tx")

# Recommended composition for the default 12-trap set (order of tens).
RECOMMENDED_COMPOSITION = {
    "plain_transfer": 3,
    "token_transfer": 3,
    "contract_interaction": 2,
    "reverted_tx": 2,
    "multi_recipient_tx": 1,
    "unknown_tx": 1,
}


@dataclass(frozen=True)
class GroundTruthProvenance:
    """How a trap's ground truth was checked against public chain data.

    Every real trap in the frozen set must carry one of these. Mock
    fixtures in tests carry mock values and are NEVER event evidence.
    """
    trap_id: str
    category: str
    source_name: str  # e.g. "BaseScan Sepolia"
    source_url: str  # full explorer/API URL of the record checked
    tx_reference: str  # must equal the trap's tx_hash
    block_reference: int | None  # must equal trap.expected_block, if set
    checked_at: str  # ISO date, e.g. "2026-11-03"
    checker: str  # who/what checked it, e.g. "manual" or script name
    notes: str = ""  # value basis, token contract, recipient list, etc.


def validate_provenance(prov: GroundTruthProvenance, trap: Trap) -> None:
    """Raise ValueError unless the provenance genuinely backs this trap."""
    if prov.trap_id != trap.trap_id:
        raise ValueError(
            f"provenance trap_id {prov.trap_id!r} does not match "
            f"trap {trap.trap_id!r}")
    if prov.category not in CATEGORY_SPECS:
        raise ValueError(f"unknown trap category: {prov.category!r}")
    spec = CATEGORY_SPECS[prov.category]
    if trap.intent != INTENT:
        raise ValueError(
            f"trap {trap.trap_id!r} intent {trap.intent!r} is not "
            f"{INTENT!r} — this catalogue is ONCHAIN_TX_LOOKUP only")
    if trap.expected_status != spec["required_status"]:
        raise ValueError(
            f"trap {trap.trap_id!r} ({prov.category}) must have status "
            f"{spec['required_status']!r}, got "
            f"{trap.expected_status!r}")
    if trap.expected_status == "pending":
        raise ValueError(
            f"trap {trap.trap_id!r}: pending transactions are never "
            f"fixed traps — their ground truth changes when they confirm")
    for fname in spec["required_fields"]:
        if getattr(trap, f"expected_{fname}") is None:
            raise ValueError(
                f"trap {trap.trap_id!r} ({prov.category}) is missing "
                f"required ground-truth field {fname!r}")
    if prov.category == "unknown_tx":
        for fname in ("from", "to", "value", "block"):
            if getattr(trap, f"expected_{fname}") is not None:
                raise ValueError(
                    f"unknown_tx trap {trap.trap_id!r} must not carry a "
                    f"{fname} ground truth — its whole point is that no "
                    f"record exists")
    if not prov.source_name or not prov.source_url:
        raise ValueError(f"trap {trap.trap_id!r}: provenance source is empty")
    if not (prov.source_url.startswith("http://")
            or prov.source_url.startswith("https://")):
        raise ValueError(
            f"trap {trap.trap_id!r}: source_url must be an http(s) URL, "
            f"got {prov.source_url!r}")
    if prov.tx_reference != trap.tx_hash:
        raise ValueError(
            f"trap {trap.trap_id!r}: provenance tx_reference does not "
            f"match the trap tx_hash")
    if trap.expected_block is not None and \
            prov.block_reference != trap.expected_block:
        raise ValueError(
            f"trap {trap.trap_id!r}: provenance block_reference "
            f"{prov.block_reference!r} does not match expected_block "
            f"{trap.expected_block!r}")
    if not prov.checked_at or not prov.checker:
        raise ValueError(
            f"trap {trap.trap_id!r}: provenance needs checked_at and checker")


def estimate_cost(n_traps: int, n_providers: int = PROVIDERS_PER_TRAP) -> dict:
    """Cost of running a set, in testnet USDC at the docs' ~$0.01/call.

    Returns calls, base cost, protocol fee and total. These are
    planning estimates from the docs figure, NOT a measured bill —
    real per-call prices come from the live 402 challenge at run time.
    """
    calls = int(n_traps) * int(n_providers)
    base = calls * COST_PER_CALL_USD
    fee = base * PROTOCOL_FEE_RATE
    return {"calls": calls, "base_usd": round(base, 4),
            "protocol_fee_usd": round(fee, 4),
            "total_usd": round(base + fee, 4)}


def build_fixed_set(entries) -> list:
    """Validate and freeze a trap set.

    entries: iterable of (Trap, GroundTruthProvenance). Returns the
    traps in order. Raises ValueError on: empty set, duplicate ids,
    over MAX_TRAPS, any provenance failure, or a set missing a
    mandatory category (reverted_tx, unknown_tx).
    """
    entries = list(entries)
    traps = [t for t, _ in entries]
    validate_trap_set(traps)
    if len(traps) > MAX_TRAPS:
        raise ValueError(
            f"fixed trap set has {len(traps)} traps, over the cap of "
            f"{MAX_TRAPS} (cost and run-time discipline)")
    categories = set()
    for trap, prov in entries:
        validate_provenance(prov, trap)
        categories.add(prov.category)
    missing = [c for c in MANDATORY_CATEGORIES if c not in categories]
    if missing:
        raise ValueError(
            f"fixed trap set is missing mandatory categories {missing}: "
            f"a set that cannot catch reverts reported as confirmed, or "
            f"hallucinated unknown transactions, is not a trap set")
    return traps
