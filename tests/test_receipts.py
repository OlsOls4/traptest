"""Tests for traptest/receipts.py — FABRICATED settlement data only.

No live receipts, no network: every receipt dict below is made up
in-test (modelled on the live log shape verified 8 Nov 2026).
"""
import base64
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traptest.receipts import (
    SETTLEMENT_AMOUNT_ATOMIC, SETTLEMENT_PAY_TO, SETTLEMENT_TOKEN,
    TRANSFER_TOPIC, decode_receipt_tx_hash, parse_json_text,
    verify_receipt_batch, verify_receipt_result,
)

PAY_TO = SETTLEMENT_PAY_TO
TOKEN = SETTLEMENT_TOKEN
PAYER = "0x170DfA67D1e37915d8130eaB9bD3b0a4E115f0C0"


def _topic(addr):
    return "0x" + "00" * 12 + addr[2:].lower()


def _transfer_log(to=PAY_TO, amount=10000, token=TOKEN):
    return {
        "address": token,
        "topics": [TRANSFER_TOPIC, _topic(PAYER), _topic(to)],
        "data": "0x" + format(amount, "064x"),
    }


def _receipt(status="0x1", logs=None):
    return {"status": status, "logs": logs if logs is not None else [_transfer_log()],
            "to": TOKEN, "transactionHash": "0x" + "aa" * 32}


class TestVerifyReceiptResult(unittest.TestCase):
    def test_exact_settlement_verifies(self):
        self.assertTrue(verify_receipt_result(_receipt()))

    def test_wrong_amount_fails(self):
        self.assertFalse(verify_receipt_result(_receipt(logs=[_transfer_log(amount=9999)])))

    def test_wrong_pay_to_fails(self):
        self.assertFalse(verify_receipt_result(
            _receipt(logs=[_transfer_log(to="0x0000000000000000000000000000000000000001")])))

    def test_wrong_token_fails(self):
        self.assertFalse(verify_receipt_result(
            _receipt(logs=[_transfer_log(token="0x1c7d4b196cb0c7b01d743fbc6116a902379c7238")])))

    def test_reverted_settlement_fails(self):
        self.assertFalse(verify_receipt_result(_receipt(status="0x0")))

    def test_no_transfer_log_fails(self):
        self.assertFalse(verify_receipt_result(_receipt(logs=[])))
        # An AuthorizationUsed-style log (different topic, payee-like
        # third topic) must NOT count as a Transfer.
        other = {"address": TOKEN,
                 "topics": ["0x98de503528ee59b575ef0c0a2576a82497bfc029a5685b209e9ec333479b10a5",
                            _topic(PAYER), _topic(PAY_TO)],
                 "data": "0x"}
        self.assertFalse(verify_receipt_result(_receipt(logs=[other])))

    def test_null_or_missing_result_fails(self):
        self.assertFalse(verify_receipt_result(None))
        self.assertFalse(verify_receipt_result({}))
        self.assertFalse(verify_receipt_result({"status": "0x1"}))

    def test_live_shape_verifies(self):
        # The exact log shape from a real 6 Nov settlement receipt
        # (tx 0xca5b…9984): Transfer, payer -> payTo, data 0x2710.
        live = _receipt(logs=[
            {"address": TOKEN,
             "topics": ["0x98de503528ee59b575ef0c0a2576a82497bfc029a5685b209e9ec333479b10a5",
                        _topic(PAYER),
                        "0xc3fb5105959e9af50ce649674f68d3dda649579843268af315d7bbd211706740"],
             "data": "0x"},
            _transfer_log(amount=0x2710)])
        self.assertTrue(verify_receipt_result(live))


class TestVerifyReceiptBatch(unittest.TestCase):
    def test_batch_verifies_each(self):
        keys = [("t01", "9002", "0x" + "aa" * 32), ("t02", "9002", "0x" + "bb" * 32)]
        recs = [{"id": 0, "result": _receipt()},
                {"id": 1, "result": _receipt(logs=[_transfer_log(amount=1)])}]
        out = verify_receipt_batch(keys, recs)
        self.assertEqual(out, {("t01", "9002"): True, ("t02", "9002"): False})

    def test_short_batch_raises_instead_of_truncating(self):
        keys = [("t01", "9002", "0x" + "aa" * 32), ("t02", "9002", "0x" + "bb" * 32)]
        with self.assertRaises(ValueError):
            verify_receipt_batch(keys, [{"id": 0, "result": _receipt()}])

    def test_long_batch_raises(self):
        keys = [("t01", "9002", "0x" + "aa" * 32)]
        with self.assertRaises(ValueError):
            verify_receipt_batch(keys, [{"id": 0, "result": _receipt()},
                                        {"id": 1, "result": _receipt()}])


class TestReceiptHelpers(unittest.TestCase):
    def test_decode_receipt_tx_hash(self):
        raw = base64.b64encode(json.dumps(
            {"tx_hash": "0x" + "cc" * 32}).encode()).decode()
        self.assertEqual(decode_receipt_tx_hash(raw), "0x" + "cc" * 32)

    def test_decode_malformed_receipt_returns_none(self):
        self.assertIsNone(decode_receipt_tx_hash("!!!not-base64!!!"))
        self.assertIsNone(decode_receipt_tx_hash(None))
        self.assertIsNone(decode_receipt_tx_hash(
            base64.b64encode(b"not json").decode()))

    def test_parse_json_text_guards_bad_json(self):
        self.assertEqual(parse_json_text('{"a": 1}', "test"), {"a": 1})
        with self.assertRaises(RuntimeError):
            parse_json_text("not json {", "test")


if __name__ == "__main__":
    unittest.main()
