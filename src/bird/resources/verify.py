"""The Verify product: ``client.verify.verifications`` — start a verification (send
a one-time passcode) and check the passcode a recipient submits.

Identify the check by the same recipient used to start it; no verification id is
stored between the two calls.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import (
    Verification,
    VerificationCheckRequest,
    VerificationCheckResult,
    VerificationCreateRequest,
)
from bird._models import to_wire
from bird._types import RequestOptions

_PATH = "/v1/verify/verifications"
_CHECK_PATH = "/v1/verify/verifications/check"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _create_body(
    *,
    email: str | None,
    phone: str | None,
    code_length: int | None,
    channels: Sequence[str] | None,
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    # Build options only from real overrides: an empty channels list means "use
    # the configured order", so it is omitted rather than sent as [] (matching the
    # other SDKs), and options is dropped entirely when neither override is set.
    options: dict[str, Any] = {}
    if code_length is not None:
        options["code_length"] = code_length
    if channels:
        options["channels"] = list(channels)
    body: dict[str, Any] = {
        "to": {"email_address": email, "phone_number": phone},
        "metadata": metadata,
    }
    if options:
        body["options"] = options
    return to_wire(VerificationCreateRequest, body)


def _check_body(*, email: str | None, phone: str | None, code: str) -> dict[str, Any]:
    return to_wire(VerificationCheckRequest, {
        "to": {"email_address": email, "phone_number": phone},
        "code": code,
    })


class Verifications:
    """Start and check verifications. Reach it via ``client.verify.verifications``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def create(
        self,
        *,
        email: str | None = None,
        phone: str | None = None,
        code_length: int | None = None,
        channels: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Verification:
        """Start a verification and send a one-time passcode to the recipient
        (``phone`` over SMS, ``email`` over email, or both). Calling again for the
        same recipient re-sends the code after the cooldown. The passcode is never
        returned; submit the recipient's entry with ``check``.

        ```python
        verification = client.verify.verifications.create(phone="+15551234567")
        print(verification.id, verification.status)
        ```
        """
        body = _create_body(
            email=email, phone=phone, code_length=code_length, channels=channels, metadata=metadata
        )
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return Verification.model_validate(response.json())

    def check(
        self,
        code: str,
        *,
        email: str | None = None,
        phone: str | None = None,
        options: RequestOptions | None = None,
    ) -> VerificationCheckResult:
        """Check a passcode a recipient submitted, identifying the verification by
        the same recipient. A wrong or expired code returns ``success=False`` with
        a ``reason`` — it is not an error; a verification already resolved is no
        longer checkable and returns a 404 error.

        ```python
        result = client.verify.verifications.check("123456", phone="+15551234567")
        print(result.success)
        ```
        """
        body = _check_body(email=email, phone=phone, code=code)
        response = self._client.request("POST", _CHECK_PATH, body=body, **_opts(options))
        return VerificationCheckResult.model_validate(response.json())


class Verify:
    """The Verify product namespace. Reach it via ``client.verify``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self.verifications = Verifications(client)


class AsyncVerifications:
    """Async mirror of `Verifications`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        email: str | None = None,
        phone: str | None = None,
        code_length: int | None = None,
        channels: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Verification:
        """Start a verification and send a one-time passcode (async)."""
        body = _create_body(
            email=email, phone=phone, code_length=code_length, channels=channels, metadata=metadata
        )
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return Verification.model_validate(response.json())

    async def check(
        self,
        code: str,
        *,
        email: str | None = None,
        phone: str | None = None,
        options: RequestOptions | None = None,
    ) -> VerificationCheckResult:
        """Check a passcode a recipient submitted (async)."""
        body = _check_body(email=email, phone=phone, code=code)
        response = await self._client.request("POST", _CHECK_PATH, body=body, **_opts(options))
        return VerificationCheckResult.model_validate(response.json())


class AsyncVerify:
    """Async Verify namespace. Reach it via ``client.verify``."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self.verifications = AsyncVerifications(client)
