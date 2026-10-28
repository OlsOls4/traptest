"""Trap definitions.

A trap is a query with KNOWN ground truth, fixed in advance. The trap set
must be fixed before scoring begins and never tuned to flatter a provider.
Ground-truth fields are checked against public chain data at build time
(from 1 Nov, in the event window) — never invented.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Trap:
    """One trap query for ONCHAIN_TX_LOOKUP (or a second trap intent)."""
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

    def __post_init__(self):
        if not self.trap_id or not self.intent or not self.tx_hash:
            raise ValueError("trap_id, intent and tx_hash are required")
        if self.expected_status not in ("confirmed", "reverted", "pending", "not_found"):
            raise ValueError(f"unknown expected_status: {self.expected_status}")
        if not self.tx_hash.startswith("0x") or len(self.tx_hash) != 66:
            raise ValueError("tx_hash must be a 0x-prefixed 32-byte hash")


def validate_trap_set(traps) -> None:
    """A trap set is valid only if ids are unique and non-empty."""
    ids = [t.trap_id for t in traps]
    if not ids:
        raise ValueError("trap set must not be empty")
    if len(ids) != len(set(ids)):
        raise ValueError("trap ids must be unique")
