"""x402 "exact" payment provider for Direct Ask (live work, 1 Nov 2026).

SECURITY — READ BEFORE USE:
- This module takes a private key as an argument and NEVER writes it
  anywhere: not to disk, not to the repo, not to logs, not to memory.
  The caller holds the key in session context only. A disposable
  testnet burner only; never a real wallet, never mainnet.
- The provider signs an EIP-3009 ``transferWithAuthorization`` for the
  USDC contract named in the challenge's ``Payment-Required`` header
  (live 1 Nov 2026: Ethereum Sepolia, eip155:11155111, token
  0xcc194e1a843B658526D0D5C431f670028582Ae17, EIP-712 name "USD Coin").
  That token is NOT Circle's faucet USDC (0x1c7d…), and signing for
  the wrong token is silently rejected with another 402. The payer
  only signs; the Telegraph facilitator settles the transfer, so payer
  gas is not needed for the "exact" scheme. A failed retry is not a
  billed served call, but it may still settle $0.01 into Telegraph
  escrow credit (observed 6 Nov 2026) — never assume a failed call
  cost $0.
- Amount: the challenge's ``amount_usd`` converted to smallest-unit
  USDC (6 decimals) — $0.01 -> 10000, matching the live challenge's
  own "Amount: 10000 uUSDC" line. The provider refuses a challenge
  with no pay_to, no amount, or an unknown settlement network.
"""
import base64
import json
import secrets
import time

from eth_account import Account

from .providers import MAX_CALL_USD, USDC_BY_NETWORK

X402_VERSION = 1

# EIP-712 token names are per-TOKEN, not per-network: Sepolia alone
# hosts Circle USDC ("USDC", 0x1c7d…) and Telegraph's accepted token
# ("USD Coin", 0xcc19…). The provider therefore takes the name from
# the challenge's header envelope first, then from the asset address,
# and refuses to sign when neither is known — signing with the wrong
# name produces a signature the facilitator cannot verify.
#
# NOTE (Council, 8 Nov 2026): the old TOKEN_NAME_BY_NETWORK map was
# DELETED, not fixed. It was dead code (nothing read it) and wrong
# for Sepolia ("USDC" — Circle's name — for a network that hosts two
# tokens with different names). A per-network name cannot be correct
# here; TOKEN_NAME_BY_ASSET above is the map that is actually used.
TOKEN_NAME_BY_ASSET = {
    "0xcc194e1a843b658526d0d5c431f670028582ae17": "USD Coin",
    "0x1c7d4b196cb0c7b01d743fbc6116a902379c7238": "USDC",
}


def _chain_id(network: str) -> int:
    """eip155:<chainId> -> int. Raises on anything else."""
    if not isinstance(network, str) or not network.startswith("eip155:"):
        raise ValueError(f"unsupported settlement network: {network!r}")
    return int(network.split(":", 1)[1])


def make_x402_provider(private_key, validity_seconds: int = 3600):
    """Return a DirectAskClient ``payment_provider`` for one burner key.

    ``private_key`` is used only to sign; it is never stored or logged.
    The returned callable takes a parsed 402 challenge dict (from
    ``providers.parse_402_challenge``) and returns ``{"X-PAYMENT": ...}``.
    """
    account = Account.from_key(private_key)
    payer = account.address

    def provider(challenge: dict) -> dict:
        network = challenge.get("network")
        pay_to = challenge.get("pay_to")
        amount_usd = challenge.get("amount_usd")
        asset = challenge.get("asset") or USDC_BY_NETWORK.get(str(network))
        if not pay_to:
            raise ValueError("402 challenge has no pay_to; refusing to sign")
        if amount_usd is None or float(amount_usd) <= 0:
            raise ValueError("402 challenge has no positive amount; refusing to sign")
        if float(amount_usd) > MAX_CALL_USD:
            # Per-call spend ceiling (F4): the signer is the last line
            # of defence — even a caller that bypasses the client's
            # check cannot sign more than $0.05 on one call.
            raise ValueError(
                f"402 challenge amount ${float(amount_usd):.2f} exceeds "
                f"the per-call ceiling of ${MAX_CALL_USD:.2f}; refusing to sign")
        if not asset:
            raise ValueError(f"no known USDC contract for network {network!r}; refusing to sign")
        chain_id = _chain_id(network)
        value = int(round(float(amount_usd) * 1_000_000))  # USDC: 6 decimals
        now = int(time.time())
        nonce = "0x" + secrets.token_hex(32)
        # validAfter is set 120s in the past, not to "now": the contract
        # requires validAfter <= the settling block's timestamp, and a
        # block's timestamp lags wall-clock time by up to a block
        # interval — signing with validAfter == wall-clock "now" reverts
        # as "authorization is not yet valid" (observed 1 Nov 2026).
        valid_after = now - 120
        token_name = (
            challenge.get("token_name")
            or TOKEN_NAME_BY_ASSET.get(str(asset).lower())
        )
        if not token_name:
            raise ValueError(
                f"no EIP-712 token name known for asset {asset}; refusing to sign")
        domain = {
            "name": token_name,
            "version": challenge.get("token_version") or "2",
            "chainId": chain_id,
            "verifyingContract": asset,
        }
        message_types = {
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ]
        }
        message = {
            "from": payer,
            "to": pay_to,
            "value": value,
            "validAfter": valid_after,
            "validBefore": now + validity_seconds,
            "nonce": nonce,
        }
        signed = account.sign_typed_data(domain, message_types, message)
        # x402 v2 (the live Telegraph challenge, x402Version 2) needs the
        # credential in the PAYMENT-SIGNATURE header, NOT X-PAYMENT (v1
        # only — the server silently ignores X-PAYMENT and re-issues the
        # 402), with the v2 payload shape: the echoed `accepted`
        # requirement + `resource` + payload, and the authorization's
        # numeric fields as STRINGS (the facilitator's verifier parses
        # them as strings; JSON numbers fail verification and the call
        # comes back 402). Verified live 6 Nov 2026: this exact shape
        # returns 200 from TxLens; X-PAYMENT, v1-shaped, and numeric
        # fields all return 402 (one wrong-token attempt returned 400
        # "Invalid payment"). The signature itself was always valid —
        # on-chain transferWithAuthorization simulation succeeds and
        # signer recovery matches the payer.
        wire_auth = {
            "from": message["from"],
            "to": message["to"],
            "value": str(message["value"]),
            "validAfter": str(message["validAfter"]),
            "validBefore": str(message["validBefore"]),
            "nonce": message["nonce"],
        }
        inner = {
            "signature": "0x" + signed.signature.hex(),
            "authorization": wire_auth,
        }
        version = challenge.get("x402_version") or X402_VERSION
        if version == 2:
            raw = challenge.get("raw") or {}
            accepted = next(
                (e for e in (raw.get("accepts") or [])
                 if isinstance(e, dict) and e.get("scheme") == "exact"),
                None)
            payload = {
                "x402Version": 2,
                "accepted": accepted,
                "resource": raw.get("resource"),
                "payload": inner,
            }
            header = base64.b64encode(
                json.dumps(payload).encode("utf-8")).decode("ascii")
            return {"PAYMENT-SIGNATURE": header}
        payload = {
            "x402Version": version,
            "scheme": "exact",
            "network": network,
            "payload": inner,
        }
        header = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
        return {"X-PAYMENT": header}

    provider.payer = payer
    return provider
