"""The webhooks resource: ``client.webhooks.unwrap`` verifies a signed event and
returns the typed, discriminated value. ``unwrap`` is synchronous on both clients
— it is pure crypto, no I/O and no transport coupling."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Mapping

import pydantic

from bird._exceptions import WebhookVerificationError, _header
from bird._generated import WebhookEvent

_DEFAULT_TOLERANCE = 300  # seconds


def _verify_and_parse(
    payload: str | bytes,
    headers: Mapping[str, str],
    secret: str | None,
    tolerance: int,
) -> WebhookEvent:
    """Standard Webhooks verification (HMAC-SHA256, ``v1`` tag) over the raw body.

    Operates on the raw request bytes and never re-serializes — re-encoding would
    break the signature. Any failure raises WebhookVerificationError.
    """
    if not secret:
        raise WebhookVerificationError("no webhook secret configured; pass secret= or set it on the client")

    raw = payload if isinstance(payload, (bytes, bytearray)) else payload.encode()
    msg_id = _header(headers, "webhook-id")
    timestamp = _header(headers, "webhook-timestamp")
    signatures = _header(headers, "webhook-signature")
    if not (msg_id and timestamp and signatures):
        raise WebhookVerificationError("missing webhook-id, webhook-timestamp, or webhook-signature header")

    try:
        sent_at = int(timestamp)
    except ValueError:
        raise WebhookVerificationError("invalid webhook-timestamp") from None
    if abs(int(time.time()) - sent_at) > tolerance:
        raise WebhookVerificationError("webhook timestamp is outside the tolerance window")

    key = secret[len("whsec_"):] if secret.startswith("whsec_") else secret
    try:
        key_bytes = base64.b64decode(key)
    except ValueError:
        raise WebhookVerificationError("invalid webhook secret") from None

    signed = msg_id.encode() + b"." + timestamp.encode() + b"." + raw
    expected = base64.b64encode(hmac.new(key_bytes, signed, hashlib.sha256).digest()).decode()
    for entry in signatures.split():
        version, _, signature = entry.partition(",")
        if version == "v1" and hmac.compare_digest(signature, expected):
            # Signature is valid, but a malformed body or unknown shape must still
            # surface as WebhookVerificationError, not a raw JSON/pydantic error.
            try:
                return WebhookEvent.model_validate(json.loads(raw))
            except (ValueError, pydantic.ValidationError) as exc:
                raise WebhookVerificationError("verified webhook payload is not a valid event") from exc
    raise WebhookVerificationError("no matching v1 signature")


class Webhooks:
    def __init__(self, secret: str | None) -> None:
        self._secret = secret

    def unwrap(self, payload: str | bytes, headers: Mapping[str, str], *, secret: str | None = None, tolerance: int = _DEFAULT_TOLERANCE) -> WebhookEvent:
        """Verify a signed webhook and return the typed event (``.root`` is the
        specific event). Pass the *raw* request body, unparsed. Raises
        ``WebhookVerificationError`` on a bad signature, stale timestamp, or
        missing headers.

        ```python
        # Pass the RAW request body (bytes) and the request headers.
        event = client.webhooks.unwrap(request.body, request.headers)
        if event.root.type == "email.delivered":
            print(event.root.data.email_id)
        ```
        """
        return _verify_and_parse(payload, headers, secret or self._secret, tolerance)


class AsyncWebhooks:
    """Async mirror of `Webhooks`. ``unwrap`` stays synchronous on both clients —
    it is pure crypto, no I/O."""

    def __init__(self, secret: str | None) -> None:
        self._secret = secret

    def unwrap(self, payload: str | bytes, headers: Mapping[str, str], *, secret: str | None = None, tolerance: int = _DEFAULT_TOLERANCE) -> WebhookEvent:
        """Verify a signed webhook and return the typed event (``.root`` is the
        specific event). Pass the *raw* request body, unparsed. Raises
        ``WebhookVerificationError`` on a bad signature, stale timestamp, or
        missing headers.

        ```python
        event = client.webhooks.unwrap(request.body, request.headers)
        if event.root.type == "email.delivered":
            ...
        ```
        """
        return _verify_and_parse(payload, headers, secret or self._secret, tolerance)
