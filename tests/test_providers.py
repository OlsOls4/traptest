"""Mocked-transport tests for the Direct Ask client — NO network, NO wallet,
NO keys, NO event evidence. Every HTTP interaction is a fake transport.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.providers import (
    DirectAskClient, PaymentRequiredError, PurchaseFailedError,
    TransportHTTPError, UnknownMinerError, _HttpResponse, parse_402_challenge,
)

INTENT = "ONCHAIN_TX_LOOKUP_GENERAL"
MINER = "9002"
# MOCK catalogue: cost_per_call "0.00" must NEVER be used as a price.
CATALOGUE = [{"id": MINER, "name": "MockMiner", "cost_per_call": "0.00"},
             {"id": "9005", "name": "OtherMiner", "cost_per_call": "0.00"}]
ANSWER = {"status": "confirmed", "from": "0xaaa", "to": "0xbbb",
          "value": "100", "block": 123}


def _json_body(obj):
    return json.dumps(obj).encode("utf-8")


class FakeTransport:
    """Records every call; scripted per (method, path-suffix) handler."""

    def __init__(self, handlers):
        self.handlers = handlers  # list of (predicate, fn) checked in order
        self.calls = []

    def __call__(self, method, url, body, headers):
        self.calls.append((method, url, dict(headers or {}), body))
        for pred, fn in self.handlers:
            if pred(method, url):
                return fn(method, url, body, headers)
        raise AssertionError(f"unexpected call {method} {url}")


def _is_miners(method, url):
    return method == "GET" and url.endswith(f"/intents/{INTENT}/miners")


def _is_ask(method, url):
    return method == "POST" and url.endswith(f"/ask/{MINER}")


def catalogue_handler(method, url, body, headers):
    return _HttpResponse(200, _json_body({"miners": CATALOGUE}),
                         {"Content-Type": "application/json"})


def served_handler(cost=0.01, receipt="mock-receipt-1"):
    def fn(method, url, body, headers):
        hdrs = {"Content-Type": "application/json"}
        if receipt is not None:
            hdrs["X-TELEGRAPH-RECEIPT"] = receipt
        return _HttpResponse(200, _json_body(
            {"answer": ANSWER, "cost_usd": cost, "signal_hash": "mock-sig-1"}), hdrs)
    return fn


def challenge_402(amount=0.01):
    def fn(method, url, body, headers):
        return TransportHTTPError(402, _json_body(
            {"amount_usd": amount, "payTo": "0xPAYTO",
             "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e"}),
            {"Content-Type": "application/json"})
    # FakeTransport expects a response, not an exception: wrap it.
    def raising(method, url, body, headers):
        raise fn(method, url, body, headers)
    return raising


class TestDirectAsk(unittest.TestCase):
    def test_free_200_captures_cost_signal_receipt(self):
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, served_handler())])
        res = DirectAskClient(transport=t).buy_result(INTENT, MINER, {"tx_hash": "0x00"})
        self.assertEqual(res.answer, ANSWER)
        self.assertEqual(res.cost_usd, 0.01)
        self.assertEqual(res.signal_hash, "mock-sig-1")
        self.assertTrue(res.receipt_present)
        self.assertEqual(res.receipt, "mock-receipt-1")
        self.assertFalse(res.charged)  # no payment was made on this path

    def test_missing_receipt_is_flagged_not_hidden(self):
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, served_handler(receipt=None))])
        res = DirectAskClient(transport=t).buy_result(INTENT, MINER, {})
        self.assertFalse(res.receipt_present)
        self.assertIsNone(res.receipt)

    def test_catalogue_price_never_used(self):
        # Catalogue says 0.00; the 402 challenge says 0.01; result must use 0.01.
        seen = {}

        def signer(challenge):
            seen["amount"] = challenge["amount_usd"]
            return {"X-PAYMENT": "mock-signed-payment"}

        t = FakeTransport([
            (_is_miners, catalogue_handler),
            (_is_ask, lambda m, u, b, h: (
                served_handler(cost=0.01)(m, u, b, h)
                if "X-PAYMENT" in h else (_ for _ in ()).throw(
                    TransportHTTPError(402, _json_body({"amount_usd": 0.01}),
                                       {})))),
        ])
        res = DirectAskClient(transport=t, payment_provider=signer).buy_result(
            INTENT, MINER, {})
        self.assertEqual(seen["amount"], 0.01)
        self.assertEqual(res.challenge_amount_usd, 0.01)
        self.assertTrue(res.charged)

    def test_402_without_signer_raises_and_does_not_retry(self):
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, challenge_402())])
        client = DirectAskClient(transport=t, payment_provider=None)
        with self.assertRaises(PaymentRequiredError) as ctx:
            client.buy_result(INTENT, MINER, {})
        self.assertEqual(ctx.exception.amount, 0.01)
        asks = [c for c in t.calls if c[0] == "POST"]
        self.assertEqual(len(asks), 1)  # exactly one attempt, no paid retry

    def test_402_with_signer_retries_with_payment_header(self):
        def ask(m, u, b, h):
            if "X-PAYMENT" in h:
                return served_handler()(m, u, b, h)
            raise TransportHTTPError(402, _json_body({"amount_usd": 0.01}), {})
        t = FakeTransport([(_is_miners, catalogue_handler), (_is_ask, ask)])
        res = DirectAskClient(
            transport=t,
            payment_provider=lambda ch: {"X-PAYMENT": "mock-signed"}).buy_result(
            INTENT, MINER, {})
        self.assertTrue(res.charged)
        self.assertTrue(res.receipt_present)
        self.assertEqual(res.cost_usd, 0.01)

    def test_402_with_unusable_price_refuses(self):
        with self.assertRaises(PaymentRequiredError):
            parse_402_challenge(402, _json_body({"amount_usd": 0}), {})
        with self.assertRaises(PaymentRequiredError):
            parse_402_challenge(402, _json_body({}), {})

    def test_402_with_wrong_asset_refuses(self):
        with self.assertRaises(PaymentRequiredError):
            parse_402_challenge(402, _json_body(
                {"amount_usd": 0.01, "asset": "0xDEAD"}), {})

    def test_failed_call_is_not_a_billed_served_call(self):
        # PurchaseFailedError.charged is False = "not billed for a
        # served answer". It does NOT mean the call cost $0: a failed
        # call can still settle $0.01 into Telegraph escrow credit
        # (observed 6 Nov 2026, $0.24 on 24 failed calls).
        def fail(m, u, b, h):
            raise TransportHTTPError(500, b"internal error", {})
        t = FakeTransport([(_is_miners, catalogue_handler), (_is_ask, fail)])
        with self.assertRaises(PurchaseFailedError) as ctx:
            DirectAskClient(transport=t).buy_result(INTENT, MINER, {})
        self.assertFalse(ctx.exception.charged)
        self.assertEqual(ctx.exception.status, 500)

    def test_error_body_is_not_a_charge(self):
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, lambda m, u, b, h: _HttpResponse(
                               200, _json_body({"error": "miner unavailable"}), {}))])
        with self.assertRaises(PurchaseFailedError):
            DirectAskClient(transport=t).buy_result(INTENT, MINER, {})

    def test_stale_miner_refused_before_any_ask(self):
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, served_handler())])
        with self.assertRaises(UnknownMinerError):
            DirectAskClient(transport=t).buy_result(INTENT, "99999", {})
        self.assertEqual([c for c in t.calls if c[0] == "POST"], [])

    def test_catalogue_refetched_on_every_buy(self):
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, served_handler())])
        client = DirectAskClient(transport=t)
        client.buy_result(INTENT, MINER, {})
        client.buy_result(INTENT, MINER, {})
        miners_calls = [c for c in t.calls if c[0] == "GET"]
        self.assertEqual(len(miners_calls), 2)

    def test_buy_dict_shape_matches_interface(self):
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, served_handler())])
        d = DirectAskClient(transport=t).buy(INTENT, MINER, {})
        for key in ("answer", "cost_usd", "signal_hash", "receipt_present"):
            self.assertIn(key, d)

    def test_live_402_shape_parses(self):
        # Exact shape observed from the live Engine 1 Nov 2026 (unpaid
        # probe; no purchase): accepts list, "$0.01" string price,
        # Sepolia settlement network, payTo, no asset field.
        live = {
            "error": "payment required",
            "accepts": [
                {"scheme": "exact", "price": "$0.01",
                 "network": "eip155:11155111",
                 "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"},
                {"scheme": "escrow", "price": "$0.01",
                 "network": "eip155:11155111",
                 "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"},
            ],
        }
        ch = parse_402_challenge(402, _json_body(live), {})
        self.assertEqual(ch["amount_usd"], 0.01)
        self.assertEqual(ch["scheme"], "exact")
        self.assertEqual(ch["network"], "eip155:11155111")
        self.assertEqual(ch["pay_to"], "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b")
        # No asset in the body: asset comes from the network map —
        # the LIVE accepted token 0xcc19… ("USD Coin"), NOT Circle
        # faucet USDC 0x1c7d… (the stale value previously asserted
        # here). Sepolia, NOT Base.
        self.assertEqual(
            ch["asset"].lower(),
            "0xcc194e1a843b658526d0d5c431f670028582ae17")

    def test_payment_required_header_envelope_wins(self):
        # The live Engine's real envelope is the Payment-Required
        # header (x402Version 2): it names the exact token, the amount
        # in smallest units, and the EIP-712 name — all absent from the
        # body. The header must win over the body fallback.
        import base64
        env = {
            "x402Version": 2,
            "accepts": [
                {"scheme": "exact", "amount": "10000",
                 "asset": "0xcc194e1a843B658526D0D5C431f670028582Ae17",
                 "extra": {"name": "USD Coin", "version": "2"},
                 "maxTimeoutSeconds": 60, "network": "eip155:11155111",
                 "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"},
            ],
        }
        header = base64.b64encode(json.dumps(env).encode()).decode()
        body = _json_body({"error": "payment required", "accepts": [
            {"scheme": "exact", "price": "$0.01",
             "network": "eip155:11155111",
             "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"}]})
        ch = parse_402_challenge(402, body, {"Payment-Required": header})
        self.assertEqual(ch["amount_usd"], 0.01)
        self.assertEqual(ch["asset"],
                         "0xcc194e1a843B658526D0D5C431f670028582Ae17")
        self.assertEqual(ch["token_name"], "USD Coin")
        self.assertEqual(ch["x402_version"], 2)

    def test_header_with_circle_asset_refused(self):
        # Header path previously skipped asset validation: a header
        # naming Circle USDC 0x1c7d… on Sepolia must now be refused,
        # exactly as the body path refuses it — 0x1c7d… is a different
        # token from the live accepted asset 0xcc19….
        import base64
        env = {
            "x402Version": 2,
            "accepts": [
                {"scheme": "exact", "amount": "10000",
                 "asset": "0x1c7d4b196cb0c7b01d743fbc6116a902379c7238",
                 "extra": {"name": "USDC", "version": "2"},
                 "maxTimeoutSeconds": 60, "network": "eip155:11155111",
                 "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"},
            ],
        }
        header = base64.b64encode(json.dumps(env).encode()).decode()
        with self.assertRaises(PaymentRequiredError):
            parse_402_challenge(402, _json_body({"error": "payment required"}),
                                {"Payment-Required": header})

    def test_body_with_circle_asset_refused(self):
        with self.assertRaises(PaymentRequiredError):
            parse_402_challenge(402, _json_body(
                {"amount_usd": 0.01, "network": "eip155:11155111",
                 "asset": "0x1c7d4b196cb0c7b01d743fbc6116a902379c7238",
                 "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"}), {})

    def test_served_call_without_cost_records_none_and_flags(self):
        # A paid call that returns no cost figure must NOT fall back
        # to the 402 challenge amount: cost_usd is None + flagged.
        def ask(m, u, b, h):
            if "X-PAYMENT" in h:
                return _HttpResponse(200, _json_body(
                    {"answer": ANSWER, "signal_hash": "mock-sig-1"}), {})
            raise TransportHTTPError(402, _json_body({"amount_usd": 0.01}), {})
        t = FakeTransport([(_is_miners, catalogue_handler), (_is_ask, ask)])
        res = DirectAskClient(
            transport=t,
            payment_provider=lambda ch: {"X-PAYMENT": "mock-signed"}).buy_result(
            INTENT, MINER, {})
        self.assertTrue(res.charged)
        self.assertIsNone(res.cost_usd)
        self.assertTrue(res.cost_missing)
        self.assertEqual(res.challenge_amount_usd, 0.01)

    def test_402_above_per_call_ceiling_refused_without_payment(self):
        # F4: a $0.06 challenge exceeds the $0.05 per-call ceiling —
        # refused before the signer is invoked, exactly one POST.
        seen = {}

        def signer(challenge):
            seen["called"] = True
            return {"X-PAYMENT": "mock-signed"}

        def challenge_sep(amount):
            def raising(method, url, body, headers):
                raise TransportHTTPError(402, _json_body(
                    {"amount_usd": amount, "payTo": "0xPAYTO",
                     "asset": "0xcc194e1a843B658526D0D5C431f670028582Ae17",
                     "network": "eip155:11155111"}), {})
            return raising

        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, challenge_sep(0.06))])
        client = DirectAskClient(transport=t, payment_provider=signer)
        with self.assertRaises(PaymentRequiredError) as ctx:
            client.buy_result(INTENT, MINER, {})
        self.assertIn("per-call ceiling", str(ctx.exception))
        self.assertNotIn("called", seen)
        self.assertEqual(len([c for c in t.calls if c[0] == "POST"]), 1)

    def test_402_at_per_call_ceiling_allowed(self):
        # Boundary: exactly $0.05 signs and serves.
        def ask(m, u, b, h):
            if "X-PAYMENT" in h:
                return served_handler()(m, u, b, h)
            raise TransportHTTPError(402, _json_body({"amount_usd": 0.05}), {})
        t = FakeTransport([(_is_miners, catalogue_handler), (_is_ask, ask)])
        res = DirectAskClient(
            transport=t,
            payment_provider=lambda ch: {"X-PAYMENT": "mock-signed"}).buy_result(
            INTENT, MINER, {})
        self.assertTrue(res.charged)
        self.assertEqual(res.challenge_amount_usd, 0.05)

    def test_spend_guard_refuses_challenge_over_remaining_cap(self):
        # F4: the runner's spend guard sees the live challenge amount
        # and refuses before payment when it would exceed the cap.
        seen = {}

        def signer(challenge):
            seen["called"] = True
            return {"X-PAYMENT": "mock-signed"}

        def challenge_sep(amount):
            def raising(method, url, body, headers):
                raise TransportHTTPError(402, _json_body(
                    {"amount_usd": amount, "payTo": "0xPAYTO",
                     "asset": "0xcc194e1a843B658526D0D5C431f670028582Ae17",
                     "network": "eip155:11155111"}), {})
            return raising

        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, challenge_sep(0.02))])
        client = DirectAskClient(
            transport=t, payment_provider=signer,
            spend_guard=lambda amount: amount <= 0.015)
        with self.assertRaises(PaymentRequiredError) as ctx:
            client.buy_result(INTENT, MINER, {})
        self.assertIn("remaining spend cap", str(ctx.exception))
        self.assertNotIn("called", seen)

    def test_miner_entry_skips_catalogue_refetch(self):
        # F12: a pre-fetched catalogue entry means zero catalogue GETs.
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, served_handler())])
        client = DirectAskClient(transport=t)
        res = client.buy_result(INTENT, MINER, {},
                                miner_entry={"id": MINER, "name": "MockMiner"})
        self.assertEqual(res.answer, ANSWER)
        self.assertEqual([c for c in t.calls if c[0] == "GET"], [])

    def test_miner_entry_for_another_miner_refused(self):
        t = FakeTransport([(_is_miners, catalogue_handler),
                           (_is_ask, served_handler())])
        with self.assertRaises(UnknownMinerError):
            DirectAskClient(transport=t).buy_result(
                INTENT, MINER, {}, miner_entry={"id": "9005"})
        self.assertEqual([c for c in t.calls if c[0] == "POST"], [])
        # A transport that RETURNS 402 (instead of raising) must also
        # retry with payment headers, not just raise.
        def ask(m, u, b, h):
            if "X-PAYMENT" in h:
                return served_handler()(m, u, b, h)
            return _HttpResponse(402, _json_body({"amount_usd": 0.01}), {})
        t = FakeTransport([(_is_miners, catalogue_handler), (_is_ask, ask)])
        res = DirectAskClient(
            transport=t,
            payment_provider=lambda ch: {"X-PAYMENT": "mock-signed"}).buy_result(
            INTENT, MINER, {})
        self.assertTrue(res.charged)
        self.assertEqual(res.cost_usd, 0.01)


class TestX402Provider(unittest.TestCase):
    """Signing only — a fresh in-test key, never persisted, never a
    real wallet. Verifies the EIP-3009 authorisation recovers to the
    signer's address with the challenge's exact amount and pay-to."""

    def test_signs_live_challenge_shape(self):
        import base64
        from eth_account import Account
        from eth_account.messages import encode_typed_data
        from traptest.x402 import make_x402_provider

        key = Account.create().key
        payer = Account.from_key(key).address
        provider = make_x402_provider(key)
        challenge = {
            "amount_usd": 0.01,
            "network": "eip155:11155111",
            "pay_to": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b",
            "asset": "0xcc194e1a843B658526D0D5C431f670028582Ae17",
            "token_name": "USD Coin",
            "token_version": "2",
            "x402_version": 2,
            # Raw v2 envelope, as parse_402_challenge returns it: the
            # provider echoes the accepted requirement + resource.
            "raw": {
                "accepts": [{
                    "scheme": "exact", "network": "eip155:11155111",
                    "amount": "10000",
                    "asset": "0xcc194e1a843B658526D0D5C431f670028582Ae17",
                    "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b",
                    "extra": {"name": "USD Coin", "version": "2"},
                }],
                "resource": {"description": "Payment required",
                             "mimeType": "application/json",
                             "url": "https://devnode.telegraphprotocol.com/engine/v1/ask/9002"},
            },
        }
        headers = provider(challenge)
        # x402 v2: PAYMENT-SIGNATURE, not X-PAYMENT (v1 only — the live
        # server silently ignores X-PAYMENT; proven 6 Nov 2026).
        self.assertIn("PAYMENT-SIGNATURE", headers)
        payload = json.loads(base64.b64decode(headers["PAYMENT-SIGNATURE"]))
        self.assertEqual(payload["x402Version"], 2)
        self.assertEqual(payload["accepted"]["scheme"], "exact")
        self.assertEqual(payload["accepted"]["amount"], "10000")
        auth = payload["payload"]["authorization"]
        self.assertEqual(auth["from"], payer)
        self.assertEqual(auth["to"], challenge["pay_to"])
        # Authorization numerics are STRINGS on the wire (the live
        # facilitator parses them as strings; JSON numbers fail).
        self.assertEqual(auth["value"], "10000")  # $0.01 in 6-decimal USDC
        self.assertEqual(provider.payer, payer)
        # Recover the signer from the EIP-712 message + signature.
        # Telegraph's accepted token's on-chain EIP-712 name is "USD Coin".
        domain = {"name": "USD Coin", "version": "2", "chainId": 11155111,
                  "verifyingContract": challenge["asset"]}
        types = {"TransferWithAuthorization": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"},
        ]}
        # Wire strings back to ints for the typed-data encoding.
        typed_auth = {**auth, "value": int(auth["value"]),
                      "validAfter": int(auth["validAfter"]),
                      "validBefore": int(auth["validBefore"])}
        msg = encode_typed_data(domain, types, typed_auth)
        recovered = Account.recover_message(
            msg, signature=bytes.fromhex(payload["payload"]["signature"][2:]))
        self.assertEqual(recovered, payer)

    def test_refuses_challenge_without_pay_to_or_network(self):
        from eth_account import Account
        from traptest.x402 import make_x402_provider

        provider = make_x402_provider(Account.create().key)
        with self.assertRaises(ValueError):
            provider({"amount_usd": 0.01, "network": "eip155:11155111"})
        with self.assertRaises(ValueError):
            provider({"amount_usd": 0.01, "network": "eip155:999999",
                      "pay_to": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b"})

    def test_refuses_challenge_above_per_call_ceiling(self):
        # F4: the signer itself refuses > $0.05, even if a caller
        # bypasses the client's check. Boundary $0.05 signs.
        import base64
        from eth_account import Account
        from traptest.x402 import make_x402_provider

        key = Account.create().key
        provider = make_x402_provider(key)
        base = {
            "network": "eip155:11155111",
            "pay_to": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b",
            "asset": "0xcc194e1a843B658526D0D5C431f670028582Ae17",
            "token_name": "USD Coin",
            "token_version": "2",
            "x402_version": 2,
            "raw": {
                "accepts": [{
                    "scheme": "exact", "network": "eip155:11155111",
                    "amount": "50000",
                    "asset": "0xcc194e1a843B658526D0D5C431f670028582Ae17",
                    "payTo": "0x3624EB012B5E998BB57B6bE6C9Cfc9c4bc5eb99b",
                    "extra": {"name": "USD Coin", "version": "2"},
                }],
                "resource": {"description": "Payment required",
                             "mimeType": "application/json",
                             "url": "https://devnode.telegraphprotocol.com/engine/v1/ask/9002"},
            },
        }
        with self.assertRaises(ValueError) as ctx:
            provider({**base, "amount_usd": 0.06})
        self.assertIn("per-call ceiling", str(ctx.exception))
        # Exactly $0.05 signs: value 50000 uUSDC on the wire.
        headers = provider({**base, "amount_usd": 0.05})
        payload = json.loads(base64.b64decode(headers["PAYMENT-SIGNATURE"]))
        self.assertEqual(payload["payload"]["authorization"]["value"], "50000")


if __name__ == "__main__":
    unittest.main()
