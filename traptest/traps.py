"""Trap definitions.

A trap is a query with KNOWN ground truth, fixed in advance. The trap set
must be fixed before scoring begins and never tuned to flatter a provider.
Ground-truth fields are checked against public chain data at build time
(from 1 Nov, in the event window) — never invented.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Trap:
    """One trap query for ONCHAIN_TX_LOOKUP_GENERAL (or a second trap intent)."""
    trap_id: str
    intent: str
    tx_hash: str
    # Expected ground truth. Only fields present here are scored; a field
    # the provider does not return is a field failure, never a pass.
    expected_status: str  # confirmed | reverted | pending | not_found
    expected_from: str | None = None
    expected_to: str | None = None
    expected_value: str | None = None  # as returned by the provider, compared as string
    expected_block: int | None = None
    # Scoring v2 opt-in (expansion set only, 9 Nov 2026): when True
    # and expected_status is "not_found", a not_found answer carrying
    # any invented from/to/value/block fails outright. Defaults to
    # False so the frozen-12 scoring path is byte-identical.
    strict_unknown: bool = False

    def __post_init__(self):
        if not self.trap_id or not self.intent or not self.tx_hash:
            raise ValueError("trap_id, intent and tx_hash are required")
        if self.expected_status not in ("confirmed", "reverted", "pending", "not_found"):
            raise ValueError(f"unknown expected_status: {self.expected_status}")
        if not self.tx_hash.startswith("0x") or len(self.tx_hash) != 66:
            raise ValueError("tx_hash must be a 0x-prefixed 32-byte hash")
        # Length + prefix alone are not enough: "0x" + "zz"*32 is 66
        # chars and would previously have passed. Reject non-hex.
        try:
            int(self.tx_hash, 16)
        except ValueError:
            raise ValueError("tx_hash must be hex (0x + 64 hex chars)") from None


def validate_trap_set(traps) -> None:
    """A trap set is valid only if ids are unique and non-empty."""
    ids = [t.trap_id for t in traps]
    if not ids:
        raise ValueError("trap set must not be empty")
    if len(ids) != len(set(ids)):
        raise ValueError("trap ids must be unique")
