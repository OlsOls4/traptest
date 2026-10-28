"""Deterministic scoring of a provider answer against trap ground truth.

Rules (deliberately strict — TrapTest's whole claim is trust):
- status must match exactly (case-insensitive). A status mismatch fails
  the trap outright, whatever else matches.
- each expected field present in the trap is scored individually;
  a missing provider field is a field failure, never a pass.
- overall pass requires status match AND every scored field to match.
- cost/receipt are recorded from the live call, never inferred.
"""
from dataclasses import dataclass

from .traps import Trap


@dataclass(frozen=True)
class FieldResult:
    field: str
    expected: str
    actual: str | None
    passed: bool


@dataclass(frozen=True)
class Score:
    trap_id: str
    provider_id: str
    passed: bool
    fields: tuple
    cost_usd: float | None = None
    signal_hash: str | None = None
    receipt_present: bool = False


def _norm(value):
    if value is None:
        return None
    return str(value).strip().lower()


def score_answer(trap: Trap, provider_id: str, answer: dict,
                 cost_usd=None, signal_hash=None,
                 receipt_present=False) -> Score:
    actual = answer or {}
    fields = []

    def check(name, expected, actual_value):
        if expected is None:
            return None
        passed = _norm(expected) == _norm(actual_value)
        result = FieldResult(name, str(expected),
                             None if actual_value is None else str(actual_value),
                             passed)
        fields.append(result)
        return passed

    status_ok = check("status", trap.expected_status, actual.get("status"))
    from_ok = check("from", trap.expected_from, actual.get("from"))
    to_ok = check("to", trap.expected_to, actual.get("to"))
    value_ok = check("value", trap.expected_value, actual.get("value"))
    block_ok = check("block", trap.expected_block, actual.get("block"))

    scored = [r for r in (status_ok, from_ok, to_ok, value_ok, block_ok)
               if r is not None]
    passed = bool(scored) and all(scored)
    return Score(trap.trap_id, provider_id, passed, tuple(fields),
                 cost_usd=cost_usd, signal_hash=signal_hash,
                 receipt_present=receipt_present)
