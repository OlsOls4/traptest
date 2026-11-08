"""Deterministic scoring of a provider answer against trap ground truth.

Rules (deliberately strict — TrapTest's whole claim is trust):
- status must match exactly (case-insensitive). A status mismatch fails
  the trap outright, whatever else matches.
- each expected field present in the trap is scored individually;
  a missing provider field is a field failure, never a pass.
- overall pass requires status match AND every scored field to match.
- cost/receipt are recorded from the live call, never inferred.

Numeric comparison (Council finding F-normalise / F-tests): ``value``
is compared as Decimal (wei) and ``block`` as int, so numerically
equal spellings compare equal — ``"100"`` vs ``"100.0"`` vs ``"0x64"``
all pass, and ``"1e-05"`` ETH normalised to wei compares equal to its
decimal form. Non-numeric values fall back to plain string comparison
(and fail unless the strings match). Addresses / status still compare
case-insensitively as strings.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

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


def _parse_decimal(value):
    """Parse a numeric value as Decimal; hex as integer. None if not numeric."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    if isinstance(value, Decimal):
        return value
    s = str(value).strip()
    if not s:
        return None
    if s.lower().startswith("0x"):
        try:
            return Decimal(int(s, 16))
        except ValueError:
            return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _parse_int(value):
    """Parse a block-like value as int. None if not numeric/integral."""
    d = _parse_decimal(value)
    if d is None or d != d.to_integral_value():
        return None
    try:
        return int(d)
    except (ValueError, OverflowError):
        return None


def _norm_value(expected, actual):
    """True when two wei amounts are numerically equal (any spelling)."""
    if expected is None or actual is None:
        return False
    exp, act = _parse_decimal(expected), _parse_decimal(actual)
    if exp is not None and act is not None:
        return exp == act
    return _norm(expected) == _norm(actual)


def _norm_block(expected, actual):
    """True when two block numbers are numerically equal (any spelling)."""
    if expected is None or actual is None:
        return False
    exp, act = _parse_int(expected), _parse_int(actual)
    if exp is not None and act is not None:
        return exp == act
    return _norm(expected) == _norm(actual)


def score_answer(trap: Trap, provider_id: str, answer: dict,
                 cost_usd=None, signal_hash=None,
                 receipt_present=False) -> Score:
    actual = answer or {}
    fields = []

    def check(name, expected, actual_value, compare=None):
        if expected is None:
            return None
        if compare is None:
            passed = _norm(expected) == _norm(actual_value)
        else:
            passed = compare(expected, actual_value)
        result = FieldResult(name, str(expected),
                             None if actual_value is None else str(actual_value),
                             passed)
        fields.append(result)
        return passed

    status_ok = check("status", trap.expected_status, actual.get("status"))
    from_ok = check("from", trap.expected_from, actual.get("from"))
    to_ok = check("to", trap.expected_to, actual.get("to"))
    value_ok = check("value", trap.expected_value, actual.get("value"),
                     compare=_norm_value)
    block_ok = check("block", trap.expected_block, actual.get("block"),
                     compare=_norm_block)

    scored = [r for r in (status_ok, from_ok, to_ok, value_ok, block_ok)
               if r is not None]
    passed = bool(scored) and all(scored)
    return Score(trap.trap_id, provider_id, passed, tuple(fields),
                 cost_usd=cost_usd, signal_hash=signal_hash,
                 receipt_present=receipt_present)
