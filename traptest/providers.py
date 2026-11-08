"""Provider client: live catalogue fetch + Direct Ask purchases.

PREP STATUS (27 Oct 2026): this module is framework code only. No live
purchase has been made, no wallet exists, no key or secret is stored here,
and no test in this repo touches the network — tests inject a fake
transport (see tests/test_providers.py).

Documented facts used (from IDEATION.md / Telegraph docs, 27 Oct 2026):
- Engine base: https://devnode.telegraphprotocol.com/engine
- Direct Ask: POST /engine/v1/ask/{minerId}. Auto-routed ask picks ONE
  miner and cannot compare competitors, so TrapTest always uses Direct Ask.
- Price is read from the LIVE 402 challenge, NEVER from the catalogue's
  ``cost_per_call`` field (which reads "0.00" and is not a price).
- Every served call returns ``cost_usd``, ``signal_hash`` and a Telegraph
  receipt in the ``X-TELEGRAPH-RECEIPT`` response header.
- Testnet is Base Sepolia (chain 84532) for the intelligence data;
  testnet USDC (Circle) on Base Sepolia is
  0x036CbD53842c5426634e7929541eC2318f3dCF7e. BUT the live 402
  challenges observed 1 Nov 2026 settle on Ethereum Sepolia
  (eip155:11155111), not Base Sepolia, regardless of the chain
  parameter — the settlement network is read from the live challenge,
  never assumed from the docs. Payments for testnet use are in
  testnet USDC, not card/mainnet spend. Docs' protocol fee: 2%.
- Failed calls CAN still settle: observed 6 Nov 2026, $0.24 settled
  into Telegraph escrow credit on 24 failed calls (Sigil + OnChain
  Intel, $0.01 each). A failed call is therefore never assumed to
  cost $0 — the on-chain Transfer to payTo is the evidence, and
  rows record escrow credit where it settled. Discovery endpoints
  are free.
- Miner IDs are NOT stable — they are re-fetched at run time and a
  purchase is refused if the miner is absent from the fresh catalogue.

Payment execution — deliberately NOT in this file:
- Paying an x402 challenge requires signing with a funded burner wallet,
  and escrow requires a confirmed escrow settlement step. Neither exists
  in prep, and no private key, seed, or secret may ever be put in this
  repo. So the client takes a caller-supplied ``payment_provider``:
  ``callable(challenge: dict) -> dict`` returning the payment headers to
  attach to the retry (e.g. an x402 ``X-PAYMENT`` header produced by the
  day-1 burner-wallet module, or caller-supplied escrow headers). With no
  provider, a 402 raises ``PaymentRequiredError`` and NO retry — and
  therefore no spend — happens. The exact live 402 challenge schema must
  be confirmed against a real 402 on day 1 before any spend; the parser
  below accepts the common x402 field spellings and rejects a challenge
  with no usable positive amount rather than guessing a price.
"""
import base64
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field

ENGINE_BASE = "https://devnode.telegraphprotocol.com/engine"
INTENTS_URL = f"{ENGINE_BASE}/v1/intents"
MINERS_URL = f"{ENGINE_BASE}/v1/intents/{{intent}}/miners"

# Base Sepolia (chain 84532) testnet USDC, per Telegraph docs.
USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
# Ethereum Sepolia accepted token, verified live 1–6 Nov 2026 from the
# 402 challenges and the on-chain settlement receipts: Telegraph's
# accepted token 0xcc194e1a843B658526D0D5C431f670028582Ae17 ("USD Coin",
# open mint, self-minted). This is NOT Circle's faucet USDC
# 0x1c7d4b196cb0c7b01d743fbc6116a902379c7238 — that address was the
# stale value previously recorded here from a funding receipt, and
# signing for it is rejected by the facilitator. A challenge naming
# the Circle token (header or body) is therefore refused, not paid.
USDC_SEPOLIA = "0xcc194e1a843B658526D0D5C431f670028582Ae17"
USDC_BY_NETWORK = {
    "eip155:84532": USDC_BASE_SEPOLIA,
    "eip155:11155111": USDC_SEPOLIA,
}
BASE_SEPOLIA_CHAIN_ID = 84532
RECEIPT_HEADER = "X-TELEGRAPH-RECEIPT"


class TelegraphError(Exception):
    """Base error for Direct Ask failures. (The ``charged`` flag on
    PurchaseFailedError means "not billed for a served answer", not
    "cost $0" — a failed call can still settle into escrow credit.)"""


class PaymentRequiredError(TelegraphError):
    """A 402 challenge was returned and no payment was made.

    Attributes: challenge (parsed dict), amount (float|None).
    A missing/zero amount is a hard error, not a free call.
    """

    def __init__(self, challenge, message="Payment required (402); no payment made"):
        super().__init__(message)
        self.challenge = challenge or {}
        self.amount = self.challenge.get("amount_usd")


class PurchaseFailedError(TelegraphError):
    """The ask failed (non-402 HTTP error or error body).

    ``charged`` is False here meaning "not billed for a served
    answer" — it does NOT mean the call cost $0: a failed call can
    still have settled $0.01 into Telegraph escrow credit (observed
    6 Nov 2026). Escrow settlement is recorded on the row, never
    assumed away from this flag.
    """

    def __init__(self, status=None, detail="", message=None):
        super().__init__(message or f"Ask failed (status {status}): {detail}")
        self.status = status
        self.detail = detail
        self.charged = False


class UnknownMinerError(TelegraphError):
    """Miner id absent from the freshly fetched catalogue. Refused pre-flight."""


@dataclass
class PurchaseResult:
    intent: str
    miner_id: str
    answer: dict
    cost_usd: float | None = None
    signal_hash: str | None = None
    receipt: str | None = None
    charged: bool = False
    challenge_amount_usd: float | None = None
    payment_mode: str | None = None
    # True when a served (charged) call returned no cost figure: the
    # cost is recorded as None, NOT silently filled in from the 402
    # challenge amount (see _served_result). A missing cost is a
    # data gap to flag, not a number to guess.
    cost_missing: bool = False

    @property
    def receipt_present(self) -> bool:
        return bool(self.receipt)

    def as_dict(self) -> dict:
        """Shape promised by the original ProviderClient interface, plus extras."""
        return {
            "answer": self.answer,
            "cost_usd": self.cost_usd,
            "signal_hash": self.signal_hash,
            "receipt_present": self.receipt_present,
            "receipt": self.receipt,
            "charged": self.charged,
            "challenge_amount_usd": self.challenge_amount_usd,
            "payment_mode": self.payment_mode,
            "cost_missing": self.cost_missing,
            "intent": self.intent,
            "miner_id": self.miner_id,
        }


# --------------------------------------------------------------------------
# Transport abstraction (stdlib only; tests inject a fake, never the network)
# --------------------------------------------------------------------------

class _HttpResponse:
    """Minimal response view shared by the real and fake transports."""

    def __init__(self, status, body, headers=None):
        self.status = status
        self.body = body if isinstance(body, (bytes, bytearray)) else bytes(body)
        self.headers = {str(k).lower(): v for k, v in (headers or {}).items()}

    def header(self, name):
        return self.headers.get(str(name).lower())

    def json(self):
        return json.loads(self.body.decode("utf-8")) if self.body else {}


class TransportHTTPError(Exception):
    def __init__(self, status, body=b"", headers=None):
        super().__init__(f"HTTP {status}")
        self.response = _HttpResponse(status, body, headers)


USER_AGENT = "TrapTest/1.0 (Telegraph Hackathon Season II evaluator; https://github.com/OlsOls4/traptest)"


def _urllib_transport(method, url, body, headers):
    headers = {**(headers or {}), "User-Agent": USER_AGENT}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return _HttpResponse(resp.status, resp.read(), dict(resp.headers))
    except urllib.error.HTTPError as e:
        raise TransportHTTPError(e.code, e.read(), dict(e.headers or {})) from e


def _as_list(data):
    if isinstance(data, dict):
        out = data.get("miners", data.get("intents", data.get("data", [])))
        return out if isinstance(out, list) else []
    return data if isinstance(data, list) else []


def fetch_intents(base_url: str = ENGINE_BASE) -> list:
    """Return the live canonical intent list (dicts with intent + miner_count)."""
    req = urllib.request.Request(f"{base_url}/v1/intents", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return _as_list(data)


def fetch_miners(intent: str, base_url: str = ENGINE_BASE) -> list:
    """Return live miners for one intent. Filter tx-hash-capable ones at call time."""
    url = f"{base_url}/v1/intents/{intent}/miners"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return _as_list(data)


def _header_get(headers, name):
    if not headers:
        return None
    if hasattr(headers, "get"):
        for key in (name, name.lower(), name.upper()):
            value = headers.get(key)
            if value is not None:
                return value
    return None


def parse_402_challenge(status, body, headers) -> dict:
    """Parse a 402 challenge into a normalised dict. Raises on unusable price.

    The Engine's REAL x402 envelope lives in the ``Payment-Required``
    response header (base64 JSON, x402Version 2), NOT in the body: the
    body ``accepts`` list omits the asset and the amount's units, while
    the header names the exact token contract, the amount in smallest
    units, and the EIP-712 token name/version. When the header is
    present it wins; the body parsing below is the fallback for
    transports that drop headers (and for the pre-1-Nov test fixtures).

    Body fallback amount spellings (x402-style, all treated as USD for
    the Engine's ``cost_usd`` accounting): amount, amount_usd, price,
    price_usd (a leading "$" and commas are stripped — the live body
    prices as "$0.01"), maxAmountRequired (smallest-unit USDC, 6
    decimals — converted). When ``accepts`` lists several schemes, the
    "exact" (x402) entry is preferred; escrow entries are recorded in
    ``raw``. When an asset address is given AND the settlement network
    is a known one, it must match that network's USDC contract; a
    mismatch raises rather than being silently accepted. When no asset
    is given, the asset is taken from the network map (live 1 Nov 2026:
    Sepolia, NOT Base Sepolia — and the header, not the map, is the
    authority when both exist).
    """
    # --- Preferred: Payment-Required header envelope (live Engine) -----
    header_val = _header_get(headers, "Payment-Required")
    if header_val:
        try:
            env = json.loads(base64.b64decode(header_val).decode("utf-8"))
        except (ValueError, TypeError):
            env = None
        if isinstance(env, dict):
            accepts = env.get("accepts")
            if isinstance(accepts, list) and accepts:
                chosen = next(
                    (e for e in accepts if isinstance(e, dict) and e.get("scheme") == "exact"),
                    accepts[0])
                if isinstance(chosen, dict):
                    try:
                        amount = float(chosen["amount"]) / 1_000_000
                    except (KeyError, TypeError, ValueError):
                        amount = None
                    if amount is not None and amount > 0:
                        extra = chosen.get("extra") or {}
                        # The header path previously skipped asset
                        # validation entirely (only the body path
                        # checked it), so a challenge naming the wrong
                        # token — e.g. Circle USDC 0x1c7d… on Sepolia
                        # instead of the accepted 0xcc19… — would have
                        # been signed. Apply the same check here:
                        # a named asset must match the network map.
                        # Decision (documented): header + Circle
                        # 0x1c7d… is REFUSED — it is a different token
                        # from the live accepted asset, and signing
                        # for it is rejected by the facilitator.
                        header_asset = chosen.get("asset")
                        header_network = chosen.get("network")
                        expected_asset = (USDC_BY_NETWORK.get(str(header_network))
                                          if header_network else None)
                        if (header_asset and expected_asset is not None
                                and str(header_asset).lower() != expected_asset.lower()):
                            raise PaymentRequiredError(
                                {"raw": env, "amount_usd": amount},
                                f"402 challenge names an asset ({header_asset}) that "
                                f"is not the known USDC for network {header_network}; "
                                f"refusing to sign for an unknown/wrong asset")
                        return {
                            "amount_usd": amount,
                            "asset": chosen.get("asset"),
                            "pay_to": chosen.get("payTo") or chosen.get("pay_to"),
                            "network": chosen.get("network"),
                            "scheme": chosen.get("scheme"),
                            "token_name": extra.get("name") if isinstance(extra, dict) else None,
                            "token_version": extra.get("version") if isinstance(extra, dict) else None,
                            "x402_version": env.get("x402Version"),
                            "raw": env,
                        }
    # --- Fallback: body --------------------------------------------------
    raw = {}
    if body:
        try:
            raw = json.loads(body.decode("utf-8")) if isinstance(body, (bytes, bytearray)) else body
        except (ValueError, UnicodeDecodeError):
            raw = {}
    if not isinstance(raw, dict):
        raw = {}
    # x402 challenges sometimes nest under "accepts" / "challenge" / "payment".
    for nest in ("accepts", "challenge", "payment"):
        nested = raw.get(nest)
        if isinstance(nested, list) and nested and all(isinstance(e, dict) for e in nested):
            chosen = next((e for e in nested if e.get("scheme") == "exact"), nested[0])
            raw = {**chosen, **{k: v for k, v in raw.items() if k != nest}}
            break
        if isinstance(nested, dict):
            raw = {**nested, **{k: v for k, v in raw.items() if k != nest}}
            break

    amount = None
    for key in ("amount_usd", "price_usd", "amount", "price"):
        if raw.get(key) is not None:
            try:
                amount = float(str(raw[key]).replace("$", "").replace(",", "").strip())
            except (TypeError, ValueError):
                continue
            break
    if amount is None and raw.get("maxAmountRequired") is not None:
        try:
            amount = float(raw["maxAmountRequired"]) / 1_000_000  # USDC: 6 decimals
        except (TypeError, ValueError):
            amount = None
    if amount is None or amount <= 0:
        raise PaymentRequiredError(
            {"raw": raw},
            "402 challenge has no usable positive price; refusing to guess a price")
    network = raw.get("network")
    asset = raw.get("asset") or raw.get("token") or _header_get(headers, "X-PAYMENT-ASSET")
    expected = USDC_BY_NETWORK.get(str(network)) if network else None
    if asset and (expected is None or str(asset).lower() != expected.lower()):
        raise PaymentRequiredError(
            {"raw": raw, "amount_usd": amount},
            f"402 challenge names an asset ({asset}) that cannot be verified as the "
            f"known USDC for network {network}; refusing to sign for an unknown asset")
    pay_to = raw.get("payTo") or raw.get("pay_to") or raw.get("payToAddress")
    return {
        "amount_usd": amount,
        "asset": asset or expected,
        "pay_to": pay_to,
        "network": network,
        "scheme": raw.get("scheme"),
        "token_name": None,
        "token_version": None,
        "x402_version": None,
        "raw": raw,
    }


def _served_result(intent, miner_id, resp, charged, challenge_amount, mode):
    data = resp.json() if resp.body else {}
    if not isinstance(data, dict):
        data = {}
    # cost_usd is the served call's own figure. When a served (paid)
    # call returns no cost figure, record None + cost_missing=True —
    # never fall back to the 402 challenge amount, which is a price
    # quote, not the call's billed cost.
    cost = data.get("cost_usd", data.get("cost"))
    try:
        cost = float(cost) if cost is not None else None
    except (TypeError, ValueError):
        cost = None
    cost_missing = bool(charged and cost is None)
    signal = data.get("signal_hash") or _header_get(resp.headers, "X-TELEGRAPH-SIGNAL-HASH")
    receipt = _header_get(resp.headers, RECEIPT_HEADER) or data.get("receipt")
    answer = data.get("answer", data.get("result", data))
    if not isinstance(answer, dict):
        answer = {"value": answer}
    return PurchaseResult(intent=intent, miner_id=miner_id, answer=answer,
                          cost_usd=cost, signal_hash=signal, receipt=receipt,
                          charged=charged, challenge_amount_usd=challenge_amount,
                          payment_mode=mode, cost_missing=cost_missing)


class ProviderClient:
    """Interface a real Direct Ask client must implement (from 1 Nov only)."""

    def buy(self, intent: str, miner_id: str, params: dict) -> dict:
        raise NotImplementedError(
            "Live purchases are event-period only (from 1 Nov) and require "
            "a funded burner wallet after the free-testnet gate passes.")


class DirectAskClient(ProviderClient):
    """Direct Ask client: fresh catalogue check, 402 handling, receipt capture.

    ``transport``: callable(method, url, body: bytes|None, headers: dict)
    returning an _HttpResponse-like object (``status``, ``body``, ``headers``)
    or raising TransportHTTPError. Defaults to urllib (real network).
    ``payment_provider``: callable(challenge: dict) -> dict of payment
    headers, or None (then any 402 raises without retrying).
    ``payment_mode``: label recorded on results, e.g. "x402" or "escrow".
    """

    def __init__(self, base_url: str = ENGINE_BASE, transport=None,
                 payment_provider=None, payment_mode: str = "x402"):
        self.base_url = base_url.rstrip("/")
        self._transport = transport or _urllib_transport
        self.payment_provider = payment_provider
        self.payment_mode = payment_mode

    # -- catalogue (re-fetched at run time, every buy) ----------------------
    def _get_json(self, url):
        resp = self._transport("GET", url, None, {"Accept": "application/json"})
        return resp.json()

    def miners(self, intent: str) -> list:
        return _as_list(self._get_json(f"{self.base_url}/v1/intents/{intent}/miners"))

    def verify_miner(self, intent: str, miner_id: str) -> dict:
        """Return the fresh catalogue entry, or raise UnknownMinerError."""
        for entry in self.miners(intent):
            if not isinstance(entry, dict):
                continue
            candidate = entry.get("id") or entry.get("miner_id") or entry.get("minerId")
            if str(candidate) == str(miner_id):
                return entry
            # Some catalogue shapes nest the id; accept a name match only
            # when the entry carries no id field at all (never on name alone
            # if an id exists and differs).
            if candidate is None and entry.get("name") == miner_id:
                return entry
        raise UnknownMinerError(
            f"miner {miner_id!r} not in freshly fetched catalogue for {intent}; "
            "refusing to buy from a stale id")

    # -- purchase ------------------------------------------------------------
    def _retry_with_payment(self, intent, miner_id, url, body, headers, challenge):
        """Retry one ask with payment headers. Raises on any failure."""
        if self.payment_provider is None:
            raise PaymentRequiredError(challenge)
        pay_headers = self.payment_provider(challenge) or {}
        if not pay_headers:
            raise PaymentRequiredError(
                challenge, "payment provider returned no payment headers; no retry made")
        try:
            paid = self._transport("POST", url, body, {**headers, **pay_headers})
        except TransportHTTPError as e2:
            raise PurchaseFailedError(
                e2.response.status,
                e2.response.body.decode("utf-8", "replace")[:500]) from e2
        if paid.status != 200:
            raise PurchaseFailedError(
                paid.status, paid.body.decode("utf-8", "replace")[:500])
        return _served_result(intent, miner_id, paid, True,
                              challenge["amount_usd"], self.payment_mode)

    def buy_result(self, intent: str, miner_id: str, params: dict,
                   verify_miner: bool = True) -> PurchaseResult:
        if verify_miner:
            # The catalogue entry is fetched and then DELIBERATELY ignored
            # for pricing: cost_per_call is not a price (see module docstring).
            self.verify_miner(intent, miner_id)
        url = f"{self.base_url}/v1/ask/{miner_id}"
        body = json.dumps({"intent": intent, "params": params or {}}).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            resp = self._transport("POST", url, body, headers)
        except TransportHTTPError as e:
            resp = e.response
            if resp.status == 402:
                challenge = parse_402_challenge(resp.status, resp.body, resp.headers)
                if self.payment_provider is None:
                    raise PaymentRequiredError(challenge)
                pay_headers = self.payment_provider(challenge) or {}
                if not pay_headers:
                    raise PaymentRequiredError(
                        challenge, "payment provider returned no payment headers; no retry made")
                retry_headers = {**headers, **pay_headers}
                try:
                    paid = self._transport("POST", url, body, retry_headers)
                except TransportHTTPError as e2:
                    # A failed retry is not a billed served call — but
                    # it may still have settled into escrow credit;
                    # surface it as a failure and let the row record
                    # any escrow, never assume $0.
                    raise PurchaseFailedError(
                        e2.response.status,
                        e2.response.body.decode("utf-8", "replace")[:500]) from e2
                if paid.status != 200:
                    raise PurchaseFailedError(
                        paid.status, paid.body.decode("utf-8", "replace")[:500])
                return _served_result(intent, miner_id, paid, True,
                                      challenge["amount_usd"], self.payment_mode)
            raise PurchaseFailedError(
                resp.status, resp.body.decode("utf-8", "replace")[:500]) from e
        if resp.status == 402:
            # Transport that returns 402 instead of raising it: same handling.
            challenge = parse_402_challenge(resp.status, resp.body, resp.headers)
            return self._retry_with_payment(intent, miner_id, url, body, headers, challenge)
        if resp.status != 200:
            raise PurchaseFailedError(
                resp.status, resp.body.decode("utf-8", "replace")[:500])
        data = resp.json() if resp.body else {}
        if isinstance(data, dict) and data.get("error"):
            # Served error body: a failed call (not a billed served
            # answer — but it may still have settled into escrow
            # credit; see module docstring).
            raise PurchaseFailedError(resp.status, str(data.get("error"))[:500])
        return _served_result(intent, miner_id, resp, False, None, None)

    def buy(self, intent: str, miner_id: str, params: dict,
            verify_miner: bool = True) -> dict:
        return self.buy_result(intent, miner_id, params,
                               verify_miner=verify_miner).as_dict()
