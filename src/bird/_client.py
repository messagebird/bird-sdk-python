"""The public clients: ``Bird`` (synchronous) and ``AsyncBird`` (asynchronous).

Both resolve configuration the same way — the API key from the ``api_key``
argument or ``BIRD_API_KEY``; the base URL from ``base_url``, ``BIRD_BASE_URL``,
or the region (explicit ``region`` or inferred from the ``bk_{region}_…`` or ``bm_{region}_…`` key
prefix). A client certificate (``client_cert`` and ``client_key``, or ``BIRD_CLIENT_CERT``
and ``BIRD_CLIENT_KEY``) is presented on every request and moves the region's host to
its mTLS endpoint. They add the escape-hatch verb methods over the request
lifecycle in ``_base_client``; resource namespaces attach on top.
"""

from __future__ import annotations

import os
import re
import ssl
from typing import Any, Mapping

import httpx
import pydantic

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._constants import DEFAULT_MAX_RETRIES
from bird._exceptions import BirdError
from bird._types import omit, EmailDefaults, Omit
from bird.resources.audiences_gen import AsyncAudiences, Audiences
from bird.resources.contact_properties_gen import AsyncContactProperties, ContactProperties
from bird.resources.contacts import AsyncContacts, Contacts
from bird.resources.domains_gen import AsyncDomains, Domains
from bird.resources.email import AsyncEmail, Email
from bird.resources.lookup_gen import AsyncLookup, Lookup
from bird.resources.sms_senders_gen import SmsSenders, AsyncSmsSenders
from bird.resources.sms_sender_requirements_gen import SmsSenderRequirements, AsyncSmsSenderRequirements
from bird.resources.sms_sender_registrations_gen import SmsSenderRegistrations, AsyncSmsSenderRegistrations
from bird.resources.billing_prices_gen import BillingPrices, AsyncBillingPrices
from bird.resources.billing_wallets_gen import BillingWallets, AsyncBillingWallets
from bird.resources.compliance_attachments import AsyncComplianceAttachments, ComplianceAttachments
from bird.resources.compliance_document_templates import (
    AsyncComplianceDocumentTemplates,
    ComplianceDocumentTemplates,
)
from bird.resources.compliance_identities_gen import AsyncComplianceIdentities, ComplianceIdentities
from bird.resources.compliance_requirements_gen import AsyncComplianceRequirements, ComplianceRequirements
from bird.resources.compliance_submissions_gen import AsyncComplianceSubmissions, ComplianceSubmissions
from bird.resources.numbers import AsyncNumbers, Numbers
from bird.resources.broadcasts import AsyncBroadcasts, Broadcasts
from bird.resources.assets import Assets, AsyncAssets
from bird.resources.preferences import AsyncPreferences, Preferences
from bird.resources.organization import AsyncOrganizationResource, OrganizationResource
from bird.resources.workspace import AsyncWorkspaceResource, WorkspaceResource
from bird.resources.realtime import AsyncRealtime, Realtime
from bird.resources.amb import AsyncAmb, Amb
from bird.resources.esim import AsyncEsim, Esim
from bird.resources.sms import AsyncSms, Sms
from bird.resources.sms_keyword_rules_gen import AsyncSmsKeywordRules, SmsKeywordRules
from bird.resources.sms_suppressions_gen import AsyncSmsSuppressions, SmsSuppressions
from bird.resources.sms_templates import AsyncSmsTemplates, SmsTemplates
from bird.resources.suppressions_gen import AsyncSuppressions, Suppressions
from bird.resources.verify import AsyncVerify, Verify
from bird.resources.voice import AsyncVoice, Voice
from bird.resources.webhooks import AsyncWebhooks, Webhooks
from bird.resources.whatsapp import AsyncWhatsapp, Whatsapp

_REGION_PREFIX = re.compile(r"^(?:bk|bm)_([a-z]{2}[0-9]+)_.+")


def _infer_region(api_key: str) -> str | None:
    match = _REGION_PREFIX.match(api_key)
    return match.group(1) if match else None


def _resolve(
    api_key: str | None, base_url: str | None, region: str | None, *, mtls: bool = False
) -> tuple[str | None, str | None]:
    """Resolve the key and base URL. Both may be None for a receiver-only client
    (webhook verification needs neither); the missing-key error is raised at the
    first API call instead of here."""
    api_key = api_key or os.environ.get("BIRD_API_KEY")
    base_url = base_url or os.environ.get("BIRD_BASE_URL")
    if not base_url:
        region = region or (_infer_region(api_key) if api_key else None)
        if region:
            base_url = f"https://mtls.{region}.platform.bird.com" if mtls else f"https://{region}.platform.bird.com"
        elif api_key:
            raise BirdError(
                "could not determine region: pass region= or base_url=, "
                "or use a bk_{region}_{token} or bm_{region}_{token} API key"
            )
    return api_key, base_url


def _client_certificate(
    client_cert: str | os.PathLike[str] | None,
    client_key: str | os.PathLike[str] | None,
    http_client: httpx.Client | httpx.AsyncClient | None,
) -> ssl.SSLContext | None:
    """Load the client certificate into an SSL context, or return None when none is
    set. The environment applies only when no ``http_client`` is passed, so the pool
    a ``with_options`` copy shares never meets a second certificate."""
    if http_client is None:
        client_cert = client_cert or os.environ.get("BIRD_CLIENT_CERT")
        client_key = client_key or os.environ.get("BIRD_CLIENT_KEY")
    if not client_cert and not client_key:
        return None
    if http_client is not None:
        raise BirdError(
            "client_cert= cannot apply to an http_client= you pass; configure the certificate on that client instead"
        )
    if not client_cert:
        raise BirdError("a client key needs its certificate: pass client_cert= or set BIRD_CLIENT_CERT")
    if not client_key:
        raise BirdError("a client certificate needs its key: pass client_key= or set BIRD_CLIENT_KEY")
    for path in (client_cert, client_key):
        if not os.path.isfile(path):
            raise BirdError(f"client certificate file not found: {os.fspath(path)}")

    def refuse_encrypted() -> str:
        raise BirdError(f"client key {os.fspath(client_key)} is encrypted; pass an unencrypted PEM key")

    # httpx's own context, so the server is verified against the same roots as a client without a certificate.
    context = httpx.create_ssl_context()
    try:
        # Without a password callable, OpenSSL prompts for an encrypted key's passphrase on stdin.
        context.load_cert_chain(client_cert, client_key, password=refuse_encrypted)
    except OSError as err:  # ssl.SSLError is an OSError too
        raise BirdError(
            f"load client certificate {os.fspath(client_cert)} with key {os.fspath(client_key)}: {err}"
        ) from err
    return context


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
    new key's region prefix unless an explicit ``base_url`` — or the
    ``BIRD_BASE_URL`` env var, the deployment-wide override _resolve honors above
    region — is set, matching the constructor's precedence."""
    merged: dict[str, Any] = {**config, "http_client": live_client}
    given = {key: value for key, value in overrides.items() if not isinstance(value, Omit)}
    if config.get("_mtls") and "http_client" in given:
        raise BirdError(
            "with_options cannot replace the http_client of a client with a client certificate. "
            "Construct a new client instead."
        )
    # api_key drives the region: a new key (or region) without an explicit
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
        realtime_key: str | None = None,
        realtime_secret: str | None = None,
        realtime_encryption_master_key: str | None = None,
        email_defaults: EmailDefaults | None = None,
        timeout: httpx.Timeout | float | None | Omit = omit,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, Any] | None = None,
        http_client: httpx.Client | None = None,
        client_cert: str | os.PathLike[str] | None = None,
        client_key: str | os.PathLike[str] | None = None,
        _mtls: bool = False,
    ) -> None:
        certificate = _client_certificate(client_cert, client_key, http_client)
        mtls = _mtls or certificate is not None
        api_key, base_url = _resolve(api_key, base_url, region, mtls=mtls)
        if not api_key and not webhook_secret:
            raise BirdError(
                "configure api_key= (or BIRD_API_KEY) for API calls, "
                "or webhook_secret= for a receiver-only client"
            )
        self._config: dict[str, Any] = {
            "api_key": api_key,
            "region": region,
            "base_url": base_url,
            "api_version": api_version,
            "webhook_secret": webhook_secret,
            "realtime_key": realtime_key,
            "realtime_secret": realtime_secret,
            "realtime_encryption_master_key": realtime_encryption_master_key,
            "email_defaults": email_defaults,
            "timeout": timeout,
            "max_retries": max_retries,
            "default_headers": default_headers,
            "default_query": default_query,
            "http_client": http_client,
            "_mtls": mtls,
        }
        # region and _mtls are kept so with_options() can re-resolve correctly, but they aren't base-client args.
        base = {k: v for k, v in self._config.items() if k not in ("webhook_secret", "realtime_key", "realtime_secret", "realtime_encryption_master_key", "email_defaults", "region", "_mtls")}
        # The extra credentials some operations require, keyed by the security scheme
        # that names them. A generated method names its schemes; the base client
        # resolves them from here.
        base["credentials"] = {
            "RealtimeKey": ("X-Realtime-Key", realtime_key, "pass realtime_key= when constructing the client"),
            "RealtimeSecret": ("X-Realtime-Secret", realtime_secret, "pass realtime_secret= when constructing the client"),
        }
        if certificate is not None:
            base["http_client"] = httpx.Client(verify=certificate)
        super().__init__(**base)
        if certificate is not None:
            self._owns_client = True
        self.webhook_secret = webhook_secret
        self.email = Email(self, email_defaults)
        self.amb = Amb(self)
        self.esim = Esim(self)
        self.sms = Sms(self)
        self.sms_templates = SmsTemplates(self)
        self.sms_suppressions = SmsSuppressions(self)
        self.sms_keyword_rules = SmsKeywordRules(self)
        self.whatsapp = Whatsapp(self)
        self.voice = Voice(self)
        self.verify = Verify(self)
        self.contacts = Contacts(self)
        self.contact_properties = ContactProperties(self)
        self.audiences = Audiences(self)
        self.domains = Domains(self)
        self.suppressions = Suppressions(self)
        self.lookup = Lookup(self)
        self.numbers = Numbers(self)
        self.assets = Assets(self)
        self.compliance_requirements = ComplianceRequirements(self)
        self.compliance_submissions = ComplianceSubmissions(self)
        self.compliance_attachments = ComplianceAttachments(self)
        self.compliance_identities = ComplianceIdentities(self)
        self.billing_wallets = BillingWallets(self)
        self.billing_prices = BillingPrices(self)
        self.sms_sender_registrations = SmsSenderRegistrations(self)
        self.sms_sender_requirements = SmsSenderRequirements(self)
        self.sms_senders = SmsSenders(self)
        self.compliance_document_templates = ComplianceDocumentTemplates(self)
        self.preferences = Preferences(self)
        self.broadcasts = Broadcasts(self, email_defaults)
        self.workspace = WorkspaceResource(self)
        self.organization = OrganizationResource(self)
        self.webhooks = Webhooks(self, webhook_secret)
        self.realtime = Realtime(self, realtime_key, realtime_secret, realtime_encryption_master_key)

    def with_options(
        self,
        *,
        api_key: str | None | Omit = omit,
        region: str | None | Omit = omit,
        base_url: str | None | Omit = omit,
        api_version: str | None | Omit = omit,
        webhook_secret: str | None | Omit = omit,
        realtime_key: str | None | Omit = omit,
        realtime_secret: str | None | Omit = omit,
        realtime_encryption_master_key: str | None | Omit = omit,
        email_defaults: EmailDefaults | None | Omit = omit,
        timeout: httpx.Timeout | float | None | Omit = omit,
        max_retries: int | Omit = omit,
        default_headers: Mapping[str, str] | None | Omit = omit,
        default_query: Mapping[str, Any] | None | Omit = omit,
        http_client: httpx.Client | None | Omit = omit,
    ) -> "Bird":
        """Return a new client with some options overridden, reusing this client's
        HTTP connection pool (the derived client never closes it) unless you pass
        your own ``http_client``. Overriding ``api_key`` or ``region`` re-resolves the
        base URL from the new key's region prefix — unless an explicit ``base_url`` or
        the ``BIRD_BASE_URL`` env var is set, which win as the deployment-wide endpoint
        (the same precedence the constructor uses)."""
        return Bird(**_with_overrides(self._config, self._client, {
            "api_key": api_key, "region": region, "base_url": base_url, "api_version": api_version,
            "webhook_secret": webhook_secret, "realtime_key": realtime_key,
            "realtime_secret": realtime_secret,
            "realtime_encryption_master_key": realtime_encryption_master_key,
            "email_defaults": email_defaults, "timeout": timeout,
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
        realtime_key: str | None = None,
        realtime_secret: str | None = None,
        realtime_encryption_master_key: str | None = None,
        email_defaults: EmailDefaults | None = None,
        timeout: httpx.Timeout | float | None | Omit = omit,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, Any] | None = None,
        http_client: httpx.AsyncClient | None = None,
        client_cert: str | os.PathLike[str] | None = None,
        client_key: str | os.PathLike[str] | None = None,
        _mtls: bool = False,
    ) -> None:
        certificate = _client_certificate(client_cert, client_key, http_client)
        mtls = _mtls or certificate is not None
        api_key, base_url = _resolve(api_key, base_url, region, mtls=mtls)
        if not api_key and not webhook_secret:
            raise BirdError(
                "configure api_key= (or BIRD_API_KEY) for API calls, "
                "or webhook_secret= for a receiver-only client"
            )
        self._config: dict[str, Any] = {
            "api_key": api_key,
            "region": region,
            "base_url": base_url,
            "api_version": api_version,
            "webhook_secret": webhook_secret,
            "realtime_key": realtime_key,
            "realtime_secret": realtime_secret,
            "realtime_encryption_master_key": realtime_encryption_master_key,
            "email_defaults": email_defaults,
            "timeout": timeout,
            "max_retries": max_retries,
            "default_headers": default_headers,
            "default_query": default_query,
            "http_client": http_client,
            "_mtls": mtls,
        }
        # region and _mtls are kept so with_options() can re-resolve correctly, but they aren't base-client args.
        base = {k: v for k, v in self._config.items() if k not in ("webhook_secret", "realtime_key", "realtime_secret", "realtime_encryption_master_key", "email_defaults", "region", "_mtls")}
        # The extra credentials some operations require, keyed by the security scheme
        # that names them. A generated method names its schemes; the base client
        # resolves them from here.
        base["credentials"] = {
            "RealtimeKey": ("X-Realtime-Key", realtime_key, "pass realtime_key= when constructing the client"),
            "RealtimeSecret": ("X-Realtime-Secret", realtime_secret, "pass realtime_secret= when constructing the client"),
        }
        if certificate is not None:
            base["http_client"] = httpx.AsyncClient(verify=certificate)
        super().__init__(**base)
        if certificate is not None:
            self._owns_client = True
        self.webhook_secret = webhook_secret
        self.email = AsyncEmail(self, email_defaults)
        self.amb = AsyncAmb(self)
        self.esim = AsyncEsim(self)
        self.sms = AsyncSms(self)
        self.sms_templates = AsyncSmsTemplates(self)
        self.sms_suppressions = AsyncSmsSuppressions(self)
        self.sms_keyword_rules = AsyncSmsKeywordRules(self)
        self.whatsapp = AsyncWhatsapp(self)
        self.voice = AsyncVoice(self)
        self.verify = AsyncVerify(self)
        self.contacts = AsyncContacts(self)
        self.contact_properties = AsyncContactProperties(self)
        self.audiences = AsyncAudiences(self)
        self.domains = AsyncDomains(self)
        self.suppressions = AsyncSuppressions(self)
        self.lookup = AsyncLookup(self)
        self.numbers = AsyncNumbers(self)
        self.assets = AsyncAssets(self)
        self.compliance_requirements = AsyncComplianceRequirements(self)
        self.compliance_submissions = AsyncComplianceSubmissions(self)
        self.compliance_attachments = AsyncComplianceAttachments(self)
        self.compliance_identities = AsyncComplianceIdentities(self)
        self.billing_wallets = AsyncBillingWallets(self)
        self.billing_prices = AsyncBillingPrices(self)
        self.sms_sender_registrations = AsyncSmsSenderRegistrations(self)
        self.sms_sender_requirements = AsyncSmsSenderRequirements(self)
        self.sms_senders = AsyncSmsSenders(self)
        self.compliance_document_templates = AsyncComplianceDocumentTemplates(self)
        self.preferences = AsyncPreferences(self)
        self.broadcasts = AsyncBroadcasts(self, email_defaults)
        self.workspace = AsyncWorkspaceResource(self)
        self.organization = AsyncOrganizationResource(self)
        self.webhooks = AsyncWebhooks(self, webhook_secret)
        self.realtime = AsyncRealtime(self, realtime_key, realtime_secret, realtime_encryption_master_key)

    def with_options(
        self,
        *,
        api_key: str | None | Omit = omit,
        region: str | None | Omit = omit,
        base_url: str | None | Omit = omit,
        api_version: str | None | Omit = omit,
        webhook_secret: str | None | Omit = omit,
        realtime_key: str | None | Omit = omit,
        realtime_secret: str | None | Omit = omit,
        realtime_encryption_master_key: str | None | Omit = omit,
        email_defaults: EmailDefaults | None | Omit = omit,
        timeout: httpx.Timeout | float | None | Omit = omit,
        max_retries: int | Omit = omit,
        default_headers: Mapping[str, str] | None | Omit = omit,
        default_query: Mapping[str, Any] | None | Omit = omit,
        http_client: httpx.AsyncClient | None | Omit = omit,
    ) -> "AsyncBird":
        """Return a new client with some options overridden, reusing this client's
        HTTP connection pool (the derived client never closes it) unless you pass
        your own ``http_client``. Overriding ``api_key`` or ``region`` re-resolves the
        base URL from the new key's region prefix — unless an explicit ``base_url`` or
        the ``BIRD_BASE_URL`` env var is set, which win as the deployment-wide endpoint
        (the same precedence the constructor uses)."""
        return AsyncBird(**_with_overrides(self._config, self._client, {
            "api_key": api_key, "region": region, "base_url": base_url, "api_version": api_version,
            "webhook_secret": webhook_secret, "realtime_key": realtime_key,
            "realtime_secret": realtime_secret,
            "realtime_encryption_master_key": realtime_encryption_master_key,
            "email_defaults": email_defaults, "timeout": timeout,
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
