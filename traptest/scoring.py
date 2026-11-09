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

Scoring v2 (expansion set only, 9 Nov 2026 — NEVER retroactive):
a trap with ``strict_unknown=True`` (new-set unknown_tx traps only)
fails outright when a ``not_found`` answer carries ANY invented
from/to/value/block field, even though those fields have no expected
value and the v1 scorer skips them. The v1 path is byte-identical:
``strict_unknown`` defaults to False and the frozen-12 traps never
set it, so their scores cannot change. See
``tests/test_scoring.py::TestScoringV2``.
"""
from dataclasses import dataclass

from .normalise import _parse_decimal  # canonical implementation (F10):
# scoring.py used to carry its own copy of _parse_decimal; the two had
# already drifted once (the t08 bug). There is now one implementation,
# in traptest/normalise.py, and this module imports it.
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

    # Scoring v2, strict-unknown rule (new set only): a not_found
    # answer must carry NO invented detail. The v1 scorer skips
    # expected-None fields, so a hallucinated from/to/value/block
    # would otherwise be unscored. Each invented field is recorded
    # as a failed field result (expected "(absent)") and fails the
    # trap outright. Only applies when the trap opts in via
    # Trap.strict_unknown; the frozen 12 never do.
    if getattr(trap, "strict_unknown", False) and \
            trap.expected_status == "not_found":
        for name in ("from", "to", "value", "block"):
            actual_value = actual.get(name)
            if actual_value is not None and str(actual_value).strip() != "":
                fields.append(FieldResult(name, "(absent)",
                                          str(actual_value), False))
                passed = False
    return Score(trap.trap_id, provider_id, passed, tuple(fields),
                 cost_usd=cost_usd, signal_hash=signal_hash,
                 receipt_present=receipt_present)


def field_accuracy(scores):
    """Field-weighted accuracy over Score objects: (correct, scored).

    Co-primary metric alongside pass rate for the expansion set
    (9 Nov 2026): pass rate is trap-level (all fields must match),
    this counts every scored field individually, so a provider that
    gets 4 of 5 fields right on every trap scores 0% pass rate but
    80% field accuracy — the two numbers together say more than
    either alone. ``scores`` may be any iterable of Score.
    """
    correct = sum(1 for s in scores for f in s.fields if f.passed)
    scored = sum(len(s.fields) for s in scores)
    return correct, scored
