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

INTENT = "ONCHAIN_TX_LOOKUP"
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

    def test_failed_call_is_not_a_charge(self):
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


if __name__ == "__main__":
    unittest.main()
