from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from bird._base_client import USER_AGENT, AsyncAPIClient, SyncAPIClient
from bird._exceptions import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
    ValidationError,
    parse_retry_after,
)

BASE = "https://eu1.platform.bird.com"


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip real backoff waits so the retry tests are fast."""
    monkeypatch.setattr("bird._base_client.time.sleep", lambda _seconds: None)

    async def _async_noop(_seconds: float) -> None:
        return None

    monkeypatch.setattr("bird._base_client.asyncio.sleep", _async_noop)


def client(**kwargs: Any) -> SyncAPIClient:
    return SyncAPIClient(base_url=BASE, api_key="bk_eu1_secret", **kwargs)


@respx.mock
def test_success_sets_auth_and_ua_and_no_idempotency_on_get() -> None:
    route = respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(200, json={"ok": True}))
    response = client().request("GET", "/v1/x")
    assert response.json() == {"ok": True}
    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Bearer bk_eu1_secret"
    assert sent.headers["user-agent"] == USER_AGENT
    assert "idempotency-key" not in sent.headers


@respx.mock
def test_rejects_off_origin_paths_before_sending() -> None:
    # A crafted path must raise before any request leaves, so the API key can
    # never reach a host other than the configured origin.
    route = respx.route().mock(return_value=httpx.Response(200))
    for path in [
        "@attacker.example/collect",  # userinfo: host becomes attacker.example
        "//attacker.example/collect",  # protocol-relative authority
        "https://attacker.example/x",  # absolute URL
        "v1/email/domains",  # bare-relative, no leading slash
    ]:
        with pytest.raises(ValueError):
            client().request("GET", path)
    assert route.call_count == 0


@respx.mock
def test_retries_5xx_then_succeeds_reusing_one_idempotency_key() -> None:
    route = respx.post(f"{BASE}/v1/email/messages").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={"id": "eml_1"})]
    )
    response = client().request("POST", "/v1/email/messages", body={"x": 1})
    assert response.status_code == 200
    assert route.call_count == 2
    keys = {call.request.headers.get("idempotency-key") for call in route.calls}
    assert len(keys) == 1 and None not in keys  # one key, reused across attempts


@respx.mock
def test_non_retryable_422_raises_parsed_validation_error() -> None:
    respx.post(f"{BASE}/v1/email/messages").mock(
        return_value=httpx.Response(
            422,
            json={"error": {"type": "validation_error", "code": "E1", "message": "bad",
                            "details": [{"param": "to", "message": "x"}]}},
        )
    )
    with pytest.raises(ValidationError) as exc:
        client().request("POST", "/v1/email/messages", body={})
    assert exc.value.code == "E1"
    assert exc.value.details[0].param == "to"


@respx.mock
def test_429_with_retry_after_is_retried() -> None:
    route = respx.get(f"{BASE}/v1/x").mock(
        side_effect=[httpx.Response(429, headers={"Retry-After": "0"}), httpx.Response(200, json={})]
    )
    client().request("GET", "/v1/x")
    assert route.call_count == 2


@respx.mock
def test_exhausted_retries_raises_final_error() -> None:
    respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(503))
    with pytest.raises(APIStatusError) as exc:
        client(max_retries=1).request("GET", "/v1/x")
    assert exc.value.status_code == 503


@respx.mock
def test_terminal_429_raises_rate_limit_error_with_retry_after() -> None:
    respx.get(f"{BASE}/v1/x").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "30"}, json={"error": {"type": "rate_limit_error"}})
    )
    with pytest.raises(RateLimitError) as exc:
        client(max_retries=0).request("GET", "/v1/x")
    assert exc.value.status_code == 429
    assert exc.value.retry_after == 30.0


@respx.mock
@pytest.mark.parametrize(
    ("status", "expected_type"),
    [(401, "auth_error"), (403, "permission_error"), (404, "not_found_error"),
     (409, "conflict_error"), (402, "billing_error")],
)
def test_status_maps_to_error_type(status: int, expected_type: str) -> None:
    respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(status))
    with pytest.raises(APIStatusError) as exc:
        client(max_retries=0).request("GET", "/v1/x")
    assert exc.value.status_code == status
    assert exc.value.type == expected_type


@respx.mock
def test_non_json_error_body_infers_type_and_default_message() -> None:
    respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(500, text="<html>oops</html>"))
    with pytest.raises(APIStatusError) as exc:
        client(max_retries=0).request("GET", "/v1/x")
    assert exc.value.type == "internal_error"
    assert "500" in exc.value.message


@respx.mock
@pytest.mark.parametrize("status", [409, 501])
def test_no_retry_statuses_fail_on_first_attempt(status: int) -> None:
    # 409 (a conflict a retry can't resolve) and 501 are excluded from retries.
    route = respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(status))
    with pytest.raises(APIStatusError):
        client(max_retries=3).request("GET", "/v1/x")
    assert route.call_count == 1


def test_parse_retry_after_branches() -> None:
    from email.utils import format_datetime
    from datetime import datetime, timedelta, timezone

    assert parse_retry_after({"Retry-After": "30"}) == 30.0
    future = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=120))
    assert parse_retry_after({"Retry-After": future}) is not None
    past = format_datetime(datetime.now(timezone.utc) - timedelta(seconds=120))
    assert parse_retry_after({"Retry-After": past}) is None  # a past date is a negative wait
    assert parse_retry_after({"Retry-After": "-5"}) is None
    assert parse_retry_after({"Retry-After": "soon"}) is None
    assert parse_retry_after({}) is None


@respx.mock
def test_transport_errors_are_caught_by_except_api_error() -> None:
    # The error tree mirrors openai/anthropic: APIConnectionError/APITimeoutError are
    # APIError subclasses, so `except APIError` covers transport failures too.
    respx.get(f"{BASE}/v1/x").mock(side_effect=httpx.ConnectTimeout("slow"))
    with pytest.raises(APIError) as exc:
        client(max_retries=0).request("GET", "/v1/x")
    assert isinstance(exc.value, APITimeoutError)  # the live raised object, not just the class tree


def test_exception_hierarchy_shape() -> None:
    from bird._exceptions import WebhookVerificationError

    assert issubclass(APIStatusError, APIError)  # status errors carry the HTTP status under APIError
    assert issubclass(RateLimitError, APIStatusError)
    assert issubclass(ValidationError, APIStatusError)
    assert issubclass(APITimeoutError, APIConnectionError)
    assert issubclass(APIConnectionError, APIError)  # transport failures are APIError too
    assert not issubclass(WebhookVerificationError, APIError)  # happens after a 200; not a request failure


@respx.mock
def test_retries_transport_error_then_succeeds() -> None:
    route = respx.get(f"{BASE}/v1/x").mock(
        side_effect=[httpx.ConnectTimeout("slow"), httpx.Response(200, json={"ok": True})]
    )
    response = client(max_retries=1).request("GET", "/v1/x")
    assert response.status_code == 200
    assert route.call_count == 2  # a transient transport error is retried, then succeeds


@respx.mock
def test_caller_cannot_override_reserved_headers() -> None:
    route = respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(200, json={}))
    client().request("GET", "/v1/x", extra_headers={"Authorization": "Bearer HACK", "X-Custom": "ok"})
    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Bearer bk_eu1_secret"
    assert sent.headers["x-custom"] == "ok"


@respx.mock
def test_connection_error_is_wrapped() -> None:
    respx.get(f"{BASE}/v1/x").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(APIConnectionError):
        client(max_retries=0).request("GET", "/v1/x")


@respx.mock
async def test_async_retries_5xx_then_succeeds() -> None:
    route = respx.post(f"{BASE}/v1/email/messages").mock(
        side_effect=[httpx.Response(500), httpx.Response(200, json={"id": "eml_1"})]
    )
    async with AsyncAPIClient(base_url=BASE, api_key="bk_eu1_secret") as client_:
        response = await client_.request("POST", "/v1/email/messages", body={})
    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
async def test_async_terminal_error_and_exhaustion() -> None:
    route = respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(503))
    async with AsyncAPIClient(base_url=BASE, api_key="bk_eu1_secret") as client_:
        with pytest.raises(APIStatusError) as exc:
            await client_.request("GET", "/v1/x", max_retries=0)
    assert exc.value.status_code == 503
    assert route.call_count == 1  # the per-call max_retries=0 override is honored


@respx.mock
async def test_async_connection_error_is_wrapped() -> None:
    respx.get(f"{BASE}/v1/x").mock(side_effect=httpx.ConnectError("boom"))
    async with AsyncAPIClient(base_url=BASE, api_key="bk_eu1_secret") as client_:
        with pytest.raises(APIConnectionError):
            await client_.request("GET", "/v1/x", max_retries=0)
