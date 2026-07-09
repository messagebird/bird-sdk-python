"""The request lifecycle shared by the sync and async clients.

``BaseClient`` owns header assembly (SDK-owned headers always win), retries with
jittered backoff that honors ``Retry-After``, a per-attempt timeout, and the
once-and-reuse idempotency key for mutations — generated once per logical call so
a retried write never double-applies (ADR-0045). ``SyncAPIClient`` and
``AsyncAPIClient`` add the transport loop; a resource method calls ``request()``
and never implements retries itself.
"""

from __future__ import annotations

import asyncio
import platform
import random
import time
import uuid
from typing import Any, Mapping, TypeVar
from urllib.parse import urlsplit

import httpx

from bird._caller import detect_caller
from bird._constants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, INITIAL_RETRY_DELAY, MAX_RETRY_DELAY
from bird._exceptions import APIConnectionError, APITimeoutError, from_response, parse_retry_after
from bird._types import NOT_GIVEN, NotGiven
from bird._version import __version__

USER_AGENT = f"bird-sdk-python/{__version__} ({platform.python_implementation().lower()}/{platform.python_version()})"

# Bird-* client-identity headers (ADR-0074): the API attributes the SDK
# surface from these, not the User-Agent. Telemetry labels only; computed once.
# Keys use the canonical wire casing (matching the Go/TS SDKs).
_CLIENT_HEADERS = {
    "Bird-Surface": "sdk-python",
    "Bird-Version": __version__,
    "Bird-Lang": platform.python_implementation().lower(),
    "Bird-Os": platform.system().lower(),
    "Bird-Arch": platform.machine().lower(),
}
# Bird-Caller (the driving agent harness) — omitted when no agent env is present.
_caller = detect_caller()
if _caller:
    _CLIENT_HEADERS["Bird-Caller"] = _caller

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# SDK-owned headers a caller's extra_headers must never override. Derived from
# _CLIENT_HEADERS so the two can't drift; matched case-insensitively.
_RESERVED_HEADERS = {"authorization", "user-agent", "x-bird-api-version", "idempotency-key"} | {
    key.lower() for key in _CLIENT_HEADERS
}

# Bound to the concrete client so `with`/`async with` preserve the subclass type
# (e.g. `with Bird(...) as c` keeps `c` typed as Bird, not SyncAPIClient).
_SyncClientT = TypeVar("_SyncClientT", bound="SyncAPIClient")
_AsyncClientT = TypeVar("_AsyncClientT", bound="AsyncAPIClient")


def _validate_request_path(base_url: str, path: str) -> None:
    """Reject a caller path that would move the API key off the configured origin.

    The verb-method escape hatch joins ``path`` onto ``base_url`` and then attaches
    the bearer token, so an unvalidated path can redirect the key to another host —
    ``//host``, ``user@host``, an absolute URL, or a bare-relative segment. Require a
    single leading slash and assert the resolved origin equals the base-URL origin.
    """
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError(f"request path must be an absolute path starting with a single '/': got {path!r}")
    base = urlsplit(base_url)
    full = urlsplit(base_url + path)
    if (full.scheme, full.netloc) != (base.scheme, base.netloc):
        raise ValueError(
            f"request path {path!r} must stay on the configured Bird API origin {base.scheme}://{base.netloc}"
        )


class BaseClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        api_version: str | None = None,
        timeout: httpx.Timeout | float | None | NotGiven = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_version = api_version
        self.max_retries = max_retries
        self.timeout: httpx.Timeout | float | None = DEFAULT_TIMEOUT if isinstance(timeout, NotGiven) else timeout
        self._default_headers = dict(default_headers or {})
        self._default_query = dict(default_query or {})

    def _headers(self, extra_headers: Mapping[str, str] | None, idempotency_key: str | None) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        headers.update(self._default_headers)
        for key, value in (extra_headers or {}).items():
            if key.lower() not in _RESERVED_HEADERS:
                headers[key] = value
        headers["Authorization"] = f"Bearer {self.api_key}"
        headers["User-Agent"] = USER_AGENT
        headers.update(_CLIENT_HEADERS)
        if self.api_version:
            headers["X-Bird-API-Version"] = self.api_version
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _build_request(
        self,
        client: httpx.Client | httpx.AsyncClient,
        method: str,
        path: str,
        *,
        body: Any,
        extra_headers: Mapping[str, str] | None,
        extra_query: Mapping[str, Any] | None,
        extra_body: Mapping[str, Any] | None,
        timeout: httpx.Timeout | float | None | NotGiven,
        idempotency_key: str | None,
    ) -> httpx.Request:
        _validate_request_path(self.base_url, path)
        if extra_body:
            body = {**(body or {}), **extra_body}
        query = {**self._default_query, **(extra_query or {})}
        return client.build_request(
            method,
            self.base_url + path,
            json=body,
            params=query or None,
            headers=self._headers(extra_headers, idempotency_key),
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
        )

    @staticmethod
    def _should_retry(response: httpx.Response) -> bool:
        # 409 is a semantic conflict a retry cannot resolve; 501 is not implemented.
        code = response.status_code
        return code == 429 or (500 <= code < 600 and code != 501)

    def _retry_delay(self, attempt: int, response: httpx.Response | None) -> float:
        if response is not None:
            advised = parse_retry_after(response.headers)
            if advised is not None:
                return min(advised, MAX_RETRY_DELAY)
        delay = min(INITIAL_RETRY_DELAY * 2**attempt, MAX_RETRY_DELAY)
        return delay * (1.0 + random.random() * 0.25)

    @staticmethod
    def _idempotency_key(method: str, given: str | None) -> str | None:
        if given is not None:
            return given
        return str(uuid.uuid4()) if method.upper() in _MUTATING_METHODS else None


class SyncAPIClient(BaseClient):
    def __init__(self, *, http_client: httpx.Client | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Own (and close) the client only when we created it. A client shared in via
        # with_options() or injected by the caller is theirs to close.
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client()

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_query: Mapping[str, Any] | None = None,
        extra_body: Mapping[str, Any] | None = None,
        timeout: httpx.Timeout | float | None | NotGiven = NOT_GIVEN,
        idempotency_key: str | None = None,
        max_retries: int | None = None,
    ) -> httpx.Response:
        request = self._build_request(
            self._client, method, path,
            body=body, extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body,
            timeout=timeout, idempotency_key=self._idempotency_key(method, idempotency_key),
        )
        retries_left = self.max_retries if max_retries is None else max_retries
        attempt = 0
        while True:
            last: httpx.Response | None = None
            try:
                response = self._client.send(request)
            except httpx.TimeoutException as exc:
                if retries_left <= 0:
                    raise APITimeoutError() from exc
            except httpx.HTTPError as exc:
                if retries_left <= 0:
                    raise APIConnectionError() from exc
            else:
                if response.is_success:
                    return response
                if retries_left <= 0 or not self._should_retry(response):
                    raise from_response(response.status_code, response.content, response.headers)
                response.close()
                last = response
            time.sleep(self._retry_delay(attempt, last))
            retries_left -= 1
            attempt += 1

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self: _SyncClientT) -> _SyncClientT:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncAPIClient(BaseClient):
    def __init__(self, *, http_client: httpx.AsyncClient | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Own (and close) the client only when we created it. A client shared in via
        # with_options() or injected by the caller is theirs to close.
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient()

    async def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        extra_headers: Mapping[str, str] | None = None,
        extra_query: Mapping[str, Any] | None = None,
        extra_body: Mapping[str, Any] | None = None,
        timeout: httpx.Timeout | float | None | NotGiven = NOT_GIVEN,
        idempotency_key: str | None = None,
        max_retries: int | None = None,
    ) -> httpx.Response:
        request = self._build_request(
            self._client, method, path,
            body=body, extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body,
            timeout=timeout, idempotency_key=self._idempotency_key(method, idempotency_key),
        )
        retries_left = self.max_retries if max_retries is None else max_retries
        attempt = 0
        while True:
            last: httpx.Response | None = None
            try:
                response = await self._client.send(request)
            except httpx.TimeoutException as exc:
                if retries_left <= 0:
                    raise APITimeoutError() from exc
            except httpx.HTTPError as exc:
                if retries_left <= 0:
                    raise APIConnectionError() from exc
            else:
                if response.is_success:
                    return response
                if retries_left <= 0 or not self._should_retry(response):
                    raise from_response(response.status_code, response.content, response.headers)
                await response.aclose()
                last = response
            await asyncio.sleep(self._retry_delay(attempt, last))
            retries_left -= 1
            attempt += 1

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self: _AsyncClientT) -> _AsyncClientT:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
