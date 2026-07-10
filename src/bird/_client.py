"""The public clients: ``Bird`` (synchronous) and ``AsyncBird`` (asynchronous).

Both resolve configuration the same way — the API key from the ``api_key``
argument or ``BIRD_API_KEY``; the base URL from ``base_url``, ``BIRD_BASE_URL``,
or the region (explicit ``region`` or inferred from the ``bk_{region}_…`` key
prefix, ADR-0036). They add the escape-hatch verb methods over the request
lifecycle in ``_base_client``; resource namespaces attach on top.
"""

from __future__ import annotations

import os
import re
from typing import Any, Mapping

import httpx
import pydantic

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._constants import DEFAULT_MAX_RETRIES
from bird._exceptions import BirdError
from bird._types import NOT_GIVEN, EmailDefaults, NotGiven
from bird.resources.audiences import AsyncAudiences, Audiences
from bird.resources.contact_properties import AsyncContactProperties, ContactProperties
from bird.resources.contacts import AsyncContacts, Contacts
from bird.resources.email import AsyncEmail, Email
from bird.resources.sms import AsyncSms, Sms
from bird.resources.sms_templates import AsyncSMSTemplates, SMSTemplates
from bird.resources.webhooks import AsyncWebhooks, Webhooks

_REGION_PREFIX = re.compile(r"^bk_([a-z]{2}[0-9]+)_")


def _infer_region(api_key: str) -> str | None:
    match = _REGION_PREFIX.match(api_key)
    return match.group(1) if match else None


def _resolve(api_key: str | None, base_url: str | None, region: str | None) -> tuple[str, str]:
    api_key = api_key or os.environ.get("BIRD_API_KEY")
    if not api_key:
        raise BirdError("missing API key: pass api_key= or set BIRD_API_KEY")
    base_url = base_url or os.environ.get("BIRD_BASE_URL")
    if not base_url:
        region = region or _infer_region(api_key)
        if not region:
            raise BirdError(
                "could not determine region: pass region= or base_url=, "
                "or use a bk_{region}_{token} API key"
            )
        base_url = f"https://{region}.platform.bird.com"
    return api_key, base_url


def _decode(response: httpx.Response, cast_to: type[pydantic.BaseModel] | None) -> Any:
    if response.status_code == 204 or not response.content:
        return None
    data = response.json()
    return cast_to.model_validate(data) if cast_to is not None else data


def _with_overrides(
    config: dict[str, Any], live_client: httpx.Client | httpx.AsyncClient, overrides: dict[str, Any]
) -> dict[str, Any]:
    """Build constructor kwargs for a client derived via ``with_options``: start from
    the parent's resolved config, reuse the live HTTP client (so the derived client
    shares the pool and doesn't own it), then apply the caller's non-default
    overrides. Overriding ``api_key`` or ``region`` re-derives the base URL from the
    new key's region prefix (ADR-0036) unless an explicit ``base_url`` — or the
    ``BIRD_BASE_URL`` env var, the deployment-wide override _resolve honors above
    region — is set, matching the constructor's precedence."""
    merged: dict[str, Any] = {**config, "http_client": live_client}
    given = {key: value for key, value in overrides.items() if not isinstance(value, NotGiven)}
    # api_key drives the region (ADR-0036): a new key (or region) without an explicit
    # base_url must re-resolve the endpoint, not inherit the parent's resolved one.
    if ("api_key" in given or "region" in given) and "base_url" not in given:
        merged.pop("base_url", None)
    merged.update(given)
    return merged


class Bird(SyncAPIClient):
    """The synchronous Bird client.

    ```python
    import os
    from bird import Bird, APIStatusError, RateLimitError

    client = Bird(api_key=os.environ["BIRD_API_KEY"])  # region inferred from the key prefix
    try:
        msg = client.email.send(from_="hello@acme.com", to=["c@x.com"], subject="Hi", html="<p>hi</p>")
    except RateLimitError as err:
        wait = err.retry_after
    except APIStatusError as err:
        print(err.status_code, err.code, err.request_id)
    ```

    Reach `client.email` and `client.webhooks`, or any other endpoint via the
    verb methods (`client.get` / `post` / …). Use it as a context manager
    (`with Bird(...) as client`) to close the underlying HTTP client.

    ```python
    from bird import EmailMessage

    message = client.get("/v1/email/messages/em_01krd...", cast_to=EmailMessage)
    client.post("/v1/some/new/endpoint", body={"key": "value"})
    ```

    A single `Bird` instance is safe to share across threads — the `httpx` client
    pools connections and every call builds its own request state — so create one
    client and reuse it rather than one per request.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        region: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        webhook_secret: str | None = None,
        email_defaults: EmailDefaults | None = None,
        timeout: httpx.Timeout | float | None | NotGiven = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, Any] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        api_key, base_url = _resolve(api_key, base_url, region)
        self._config: dict[str, Any] = {
            "api_key": api_key,
            "region": region,
            "base_url": base_url,
            "api_version": api_version,
            "webhook_secret": webhook_secret,
            "email_defaults": email_defaults,
            "timeout": timeout,
            "max_retries": max_retries,
            "default_headers": default_headers,
            "default_query": default_query,
            "http_client": http_client,
        }
        # region is kept so with_options() can re-resolve correctly, but it isn't a base-client arg.
        super().__init__(**{k: v for k, v in self._config.items() if k not in ("webhook_secret", "email_defaults", "region")})
        self.webhook_secret = webhook_secret
        self.email = Email(self, email_defaults)
        self.sms = Sms(self)
        self.sms_templates = SMSTemplates(self)
        self.contacts = Contacts(self)
        self.contact_properties = ContactProperties(self)
        self.audiences = Audiences(self)
        self.webhooks = Webhooks(webhook_secret)

    def with_options(
        self,
        *,
        api_key: str | None | NotGiven = NOT_GIVEN,
        region: str | None | NotGiven = NOT_GIVEN,
        base_url: str | None | NotGiven = NOT_GIVEN,
        api_version: str | None | NotGiven = NOT_GIVEN,
        webhook_secret: str | None | NotGiven = NOT_GIVEN,
        email_defaults: EmailDefaults | None | NotGiven = NOT_GIVEN,
        timeout: httpx.Timeout | float | None | NotGiven = NOT_GIVEN,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None | NotGiven = NOT_GIVEN,
        default_query: Mapping[str, Any] | None | NotGiven = NOT_GIVEN,
        http_client: httpx.Client | None | NotGiven = NOT_GIVEN,
    ) -> "Bird":
        """Return a new client with some options overridden, reusing this client's
        HTTP connection pool (the derived client never closes it) unless you pass
        your own ``http_client``. Overriding ``api_key`` or ``region`` re-resolves the
        base URL from the new key's region prefix — unless an explicit ``base_url`` or
        the ``BIRD_BASE_URL`` env var is set, which win as the deployment-wide endpoint
        (the same precedence the constructor uses)."""
        return Bird(**_with_overrides(self._config, self._client, {
            "api_key": api_key, "region": region, "base_url": base_url, "api_version": api_version,
            "webhook_secret": webhook_secret, "email_defaults": email_defaults, "timeout": timeout,
            "max_retries": max_retries, "default_headers": default_headers, "default_query": default_query,
            "http_client": http_client,
        }))

    def get(self, path: str, *, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(self.request("GET", path, **options), cast_to)

    def post(self, path: str, *, body: Any = None, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(self.request("POST", path, body=body, **options), cast_to)

    def put(self, path: str, *, body: Any = None, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(self.request("PUT", path, body=body, **options), cast_to)

    def patch(self, path: str, *, body: Any = None, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(self.request("PATCH", path, body=body, **options), cast_to)

    def delete(self, path: str, *, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(self.request("DELETE", path, **options), cast_to)


class AsyncBird(AsyncAPIClient):
    """The asynchronous Bird client — the async mirror of `Bird`.

    ```python
    async with AsyncBird(api_key="bk_eu1_...") as client:
        msg = await client.email.send(from_="hello@acme.com", to=["c@x.com"], subject="Hi", text="hi")
    ```

    A single `AsyncBird` instance is safe to share across concurrent tasks (e.g.
    `asyncio.gather`) — reuse one client rather than creating one per request.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        region: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        webhook_secret: str | None = None,
        email_defaults: EmailDefaults | None = None,
        timeout: httpx.Timeout | float | None | NotGiven = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, Any] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        api_key, base_url = _resolve(api_key, base_url, region)
        self._config: dict[str, Any] = {
            "api_key": api_key,
            "region": region,
            "base_url": base_url,
            "api_version": api_version,
            "webhook_secret": webhook_secret,
            "email_defaults": email_defaults,
            "timeout": timeout,
            "max_retries": max_retries,
            "default_headers": default_headers,
            "default_query": default_query,
            "http_client": http_client,
        }
        # region is kept so with_options() can re-resolve correctly, but it isn't a base-client arg.
        super().__init__(**{k: v for k, v in self._config.items() if k not in ("webhook_secret", "email_defaults", "region")})
        self.webhook_secret = webhook_secret
        self.email = AsyncEmail(self, email_defaults)
        self.sms = AsyncSms(self)
        self.sms_templates = AsyncSMSTemplates(self)
        self.contacts = AsyncContacts(self)
        self.contact_properties = AsyncContactProperties(self)
        self.audiences = AsyncAudiences(self)
        self.webhooks = AsyncWebhooks(webhook_secret)

    def with_options(
        self,
        *,
        api_key: str | None | NotGiven = NOT_GIVEN,
        region: str | None | NotGiven = NOT_GIVEN,
        base_url: str | None | NotGiven = NOT_GIVEN,
        api_version: str | None | NotGiven = NOT_GIVEN,
        webhook_secret: str | None | NotGiven = NOT_GIVEN,
        email_defaults: EmailDefaults | None | NotGiven = NOT_GIVEN,
        timeout: httpx.Timeout | float | None | NotGiven = NOT_GIVEN,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None | NotGiven = NOT_GIVEN,
        default_query: Mapping[str, Any] | None | NotGiven = NOT_GIVEN,
        http_client: httpx.AsyncClient | None | NotGiven = NOT_GIVEN,
    ) -> "AsyncBird":
        """Return a new client with some options overridden, reusing this client's
        HTTP connection pool (the derived client never closes it) unless you pass
        your own ``http_client``. Overriding ``api_key`` or ``region`` re-resolves the
        base URL from the new key's region prefix — unless an explicit ``base_url`` or
        the ``BIRD_BASE_URL`` env var is set, which win as the deployment-wide endpoint
        (the same precedence the constructor uses)."""
        return AsyncBird(**_with_overrides(self._config, self._client, {
            "api_key": api_key, "region": region, "base_url": base_url, "api_version": api_version,
            "webhook_secret": webhook_secret, "email_defaults": email_defaults, "timeout": timeout,
            "max_retries": max_retries, "default_headers": default_headers, "default_query": default_query,
            "http_client": http_client,
        }))

    async def get(self, path: str, *, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(await self.request("GET", path, **options), cast_to)

    async def post(self, path: str, *, body: Any = None, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(await self.request("POST", path, body=body, **options), cast_to)

    async def put(self, path: str, *, body: Any = None, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(await self.request("PUT", path, body=body, **options), cast_to)

    async def patch(self, path: str, *, body: Any = None, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(await self.request("PATCH", path, body=body, **options), cast_to)

    async def delete(self, path: str, *, cast_to: type[pydantic.BaseModel] | None = None, **options: Any) -> Any:
        return _decode(await self.request("DELETE", path, **options), cast_to)
