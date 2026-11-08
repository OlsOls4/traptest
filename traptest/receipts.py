"""On-chain settlement-receipt verification (Council finding F-receipt).

The old code marked a receipt ``receipt_verified_onchain`` when the
Sepolia receipt's ``status`` was ``"0x1"`` alone — it never checked
that the settlement actually paid the right amount to the right
payee, and ``zip(tx_hashes, recs)`` silently truncated when the RPC
batch came back short.

A receipt now verifies only when ALL of these hold for the
``eth_getTransactionReceipt`` result of the settlement tx:
- ``status == "0x1"`` (the settlement tx succeeded), AND
- the receipt carries an ERC-20 ``Transfer`` log from the accepted
  token contract (``SETTLEMENT_TOKEN``) whose recipient (``topics[2]``)
  is ``SETTLEMENT_PAY_TO`` and whose amount (``data``) is
  ``SETTLEMENT_AMOUNT_ATOMIC`` (10000 = $0.01 in 6-decimal USDC).

That log shape is the live one, verified 8 Nov 2026 against a real
settlement receipt (tx
``0xca5bfa75ae22f984b7d75857bd64e3f364ff68950ed8df77372ccc8a870d9984``):
Transfer from burner 3 to payTo ``0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b``
for ``0x2710`` (10000). Note the receipt also carries an
``AuthorizationUsed`` log whose ``topics[2]`` is NOT the payee — only
logs with the Transfer topic count.

Helpers here are pure (no network, no subprocess) so they are unit
testable with fabricated settlement data; the run scripts only fetch
the receipts and call :func:`verify_receipt_batch`.
"""
import base64
import binascii
import json

# Live settlement constants (6 Nov 2026 run; also in scripts/full_run.py
# and scripts/mini_run.py as TOKEN / payTo — keep in sync).
SETTLEMENT_TOKEN = "0xcc194e1a843B658526D0D5C431f670028582Ae17"
SETTLEMENT_PAY_TO = "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"
SETTLEMENT_AMOUNT_ATOMIC = 10000  # $0.01 in 6-decimal USDC
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def parse_json_text(text, what="JSON"):
    """json.loads with a guarded, diagnosable failure (never bare)."""
    try:
        return json.loads(text)
    except (ValueError, TypeError) as e:
        raise RuntimeError(f"could not parse {what} as JSON: {e}; "
                           f"first 300 chars: {str(text)[:300]!r}") from e


def decode_receipt_tx_hash(receipt_b64):
    """Tx hash inside a base64 Telegraph receipt, or None if undecodable.

    Never raises: a malformed receipt is unverified, not a crash.
    """
    if not receipt_b64:
        return None
    try:
        dec = json.loads(base64.b64decode(receipt_b64).decode("utf-8"))
    except (ValueError, TypeError, binascii.Error, UnicodeDecodeError):
        return None
    if not isinstance(dec, dict):
        return None
    tx_hash = dec.get("tx_hash")
    return tx_hash if isinstance(tx_hash, str) and tx_hash else None


def _topic_address(topic):
    """Last 40 hex chars of a 32-byte topic as a 0x-address, or None."""
    if not isinstance(topic, str):
        return None
    t = topic.strip().lower()
    if t.startswith("0x"):
        t = t[2:]
    if len(t) != 64 or any(c not in "0123456789abcdef" for c in t):
        return None
    return "0x" + t[-40:]


def _log_amount(data):
    """uint256 log data as int, or None."""
    if not isinstance(data, str):
        return None
    try:
        return int(data, 16)
    except ValueError:
        return None


def verify_receipt_result(result, amount_atomic=SETTLEMENT_AMOUNT_ATOMIC,
                          pay_to=SETTLEMENT_PAY_TO,
                          token=SETTLEMENT_TOKEN):
    """True only if the receipt proves the exact settlement.

    ``result`` is one ``eth_getTransactionReceipt`` result dict (or
    None). Checks status, then the Transfer log amount + payee.
    """
    if not isinstance(result, dict):
        return False
    if result.get("status") != "0x1":
        return False
    pay_to = (pay_to or "").lower()
    token = (token or "").lower()
    for log in result.get("logs") or []:
        if not isinstance(log, dict):
            continue
        if (log.get("address") or "").lower() != token:
            continue
        topics = log.get("topics") or []
        if len(topics) < 3 or (topics[0] or "").lower() != TRANSFER_TOPIC:
            continue
        if _topic_address(topics[2]) != pay_to:
            continue
        if _log_amount(log.get("data")) != amount_atomic:
            continue
        return True
    return False


def verify_receipt_batch(keys_tx_hashes, recs, **kwargs):
    """Verify a batch of receipts. Returns {(trap_id, provider_id): bool}.

    ``keys_tx_hashes`` is a list of ``(trap_id, provider_id, tx_hash)``
    and ``recs`` the matching list of JSON-RPC response dicts, in the
    same order. Raises ValueError when the response list is shorter
    (or longer) than requested — a short batch must never silently
    verify a subset via zip truncation.
    """
    if len(recs) != len(keys_tx_hashes):
        raise ValueError(
            f"receipt batch length mismatch: requested "
            f"{len(keys_tx_hashes)} receipts, got {len(recs)}; refusing "
            f"to verify a partial batch")
    verified = {}
    for (tid, mid, _tx_hash), rec in zip(keys_tx_hashes, recs):
        res = rec.get("result") if isinstance(rec, dict) else None
        verified[(tid, mid)] = verify_receipt_result(res, **kwargs)
    return verified
