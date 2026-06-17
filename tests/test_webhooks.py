from __future__ import annotations

import base64
import hashlib
import hmac
import time

import pytest

from bird import Bird, WebhookEvent, WebhookVerificationError

SECRET = "whsec_" + base64.b64encode(b"0123456789abcdef").decode()


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret", webhook_secret=SECRET)


def _headers(payload: bytes, secret: str = SECRET, msg_id: str = "msg_1", timestamp: str | None = None) -> dict[str, str]:
    timestamp = timestamp or str(int(time.time()))
    key = base64.b64decode(secret[len("whsec_"):])
    signed = msg_id.encode() + b"." + timestamp.encode() + b"." + payload
    signature = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    return {"webhook-id": msg_id, "webhook-timestamp": timestamp, "webhook-signature": f"v1,{signature}"}


def test_unwrap_verifies_and_returns_typed_event() -> None:
    payload = b'{"type":"domain.failed","timestamp":"2026-06-01T17:00:12Z","data":{}}'
    event = client().webhooks.unwrap(payload, _headers(payload))
    assert isinstance(event, WebhookEvent)
    assert event.root.type == "domain.failed"


def test_unwrap_rejects_tampered_signature() -> None:
    payload = b'{"type":"domain.failed"}'
    headers = _headers(payload)
    headers["webhook-signature"] = "v1,deadbeef"
    with pytest.raises(WebhookVerificationError):
        client().webhooks.unwrap(payload, headers)


def test_unwrap_rejects_stale_timestamp() -> None:
    payload = b'{"type":"domain.failed"}'
    stale = str(int(time.time()) - 10_000)
    with pytest.raises(WebhookVerificationError):
        client().webhooks.unwrap(payload, _headers(payload, timestamp=stale))


def test_unwrap_rejects_missing_headers() -> None:
    with pytest.raises(WebhookVerificationError):
        client().webhooks.unwrap(b'{"type":"domain.failed"}', {"webhook-id": "msg_1"})


def test_unwrap_without_secret_raises() -> None:
    payload = b'{"type":"domain.failed"}'
    with pytest.raises(WebhookVerificationError):
        Bird(api_key="bk_eu1_secret").webhooks.unwrap(payload, _headers(payload))


def test_unwrap_valid_signature_invalid_body_raises_verification_error() -> None:
    # A correctly-signed but malformed body must surface as WebhookVerificationError,
    # not a raw JSONDecodeError leaking past the BirdError contract.
    payload = b"not json at all"
    with pytest.raises(WebhookVerificationError):
        client().webhooks.unwrap(payload, _headers(payload))
