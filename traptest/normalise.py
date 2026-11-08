"""Shared answer normalisation — the single implementation.

Moved here from the duplicated copies in scripts/full_run.py and
scripts/mini_run.py (Council finding F-normalise): the two copies had
drifted into the same bug, and a fix in one would not have reached the
other. Both scripts now import :func:`normalise` from here.

Rules (documented, because unit choice is where the old bug lived):
- ``block_number`` -> ``block`` (only when ``block`` is absent).
  A hex block (``"0x7b"``) or a decimal string (``"123"``) is
  canonicalised to an ``int``; an unparseable value is kept as-is.
- ``value_eth`` -> ``value`` (wei, as a decimal string). ``value_eth``
  is an amount in ETH, so it is converted with ``Decimal``:
  ``"0.001"`` -> ``"1000000000000000"``, ``"1e-05"`` (scientific
  notation, no decimal point — the Truvian t08 case) ->
  ``"10000000000000"``, integer ``1`` -> ``"1000000000000000000"``
  (1 ETH, NOT 1 wei — the old code passed integers through as-is,
  silently treating ETH as wei; live integers were all 0, so no live
  row changes). A hex ``value_eth`` (``"0x64"``) is a raw on-chain
  quantity and is read as wei directly -> ``"100"``.
- An already-present ``value`` is canonicalised the same way a wei
  amount is: hex -> decimal, ``"100.0"`` -> ``"100"``; a
  non-numeric value is left as-is for the scorer to fail on.
- ``None`` / missing keys are left absent (a missing provider field
  is a scoring failure, never a pass); ``normalise(None)`` returns
  ``({}, [])``.
"""
from decimal import Decimal, InvalidOperation

WEI_PER_ETH = 10 ** 18


def _parse_decimal(value):
    """Parse a numeric value as Decimal; hex strings as integer wei.

    Returns None when the value is not numeric. Floats go through
    str() so 1e-05 (float) parses as Decimal("1e-05"), not as a
    binary-float approximation.
    """
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
    """Parse a block-like value as int; hex and '123.0' both work."""
    d = _parse_decimal(value)
    if d is None or d != d.to_integral_value():
        return None
    try:
        return int(d)
    except (ValueError, OverflowError):
        return None


def _canonical_wei(value):
    """Canonical decimal-string form of a wei amount, or None."""
    d = _parse_decimal(value)
    if d is None:
        return None
    if d != d.to_integral_value():
        return None
    return str(int(d))


def normalise(answer):
    """Map provider field names to the scorer's canonical keys.

    Returns ``(normalised_answer, notes_list)``. The input dict is
    never mutated; the raw answer is always kept alongside the
    normalised one by callers, so every score stays auditable.
    """
    out = dict(answer or {})
    notes = []
    if "block" not in out and out.get("block_number") is not None:
        raw = out.pop("block_number")
        parsed = _parse_int(raw)
        out["block"] = parsed if parsed is not None else raw
        notes.append("block_number -> block")
    elif out.get("block") is not None:
        parsed = _parse_int(out["block"])
        if parsed is not None and out["block"] != parsed:
            out["block"] = parsed
            notes.append("block canonicalised to int")
    if "value" not in out and out.get("value_eth") is not None:
        raw = out.pop("value_eth")
        s = str(raw).strip()
        if s.lower().startswith("0x"):
            wei = _canonical_wei(raw)
            out["value"] = wei if wei is not None else s
            notes.append(f"value_eth {s} (hex, wei) -> {out['value']} wei")
        else:
            eth = _parse_decimal(raw)
            if eth is None:
                out["value"] = s
                notes.append(f"value_eth {s} unparseable -> value as-is")
            else:
                out["value"] = str(int(eth * WEI_PER_ETH))
                notes.append(f"value_eth {s} ETH -> {out['value']} wei")
    elif out.get("value") is not None:
        canon = _canonical_wei(out["value"])
        if canon is not None and str(out["value"]) != canon:
            out["value"] = canon
            notes.append("value canonicalised to decimal wei")
    return out, notes
