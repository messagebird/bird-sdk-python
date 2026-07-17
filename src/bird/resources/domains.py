"""Domains: ``client.domains`` — register and manage sending domains via the API.

Register a domain, publish the DNS records it returns, then call :meth:`verify`
until it is usable as a sender. ``return_path`` and ``tracking`` are the name
part only — Bird appends the sending domain (``links`` on ``mail.acme.com``
becomes ``links.mail.acme.com``).
"""

from __future__ import annotations

from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import Domain, DomainCreate, DomainUpdate
from bird._models import to_wire_exclude_unset
from bird._types import NOT_GIVEN, NotGiven, RequestOptions
from bird.pagination import AsyncPage, SyncPage

_PATH = "/v1/email/domains"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _create_body(
    *,
    domain: str,
    return_path: str | None,
    tracking: str | None,
    dkim_mode: str | None,
    click_tracking: bool | None,
    open_tracking: bool | None,
) -> dict[str, Any]:
    data: dict[str, Any] = {"domain": domain}
    settings = _settings(click_tracking, open_tracking)
    if settings:
        data["settings"] = settings
    if tracking is not None:
        data["tracking"] = {"name": tracking}
    if return_path is not None:
        data["return_path"] = {"name": return_path}
    if dkim_mode is not None:
        data["dkim"] = {"mode": dkim_mode}
    # exclude_unset so a nested toggle's False default (DomainSettings) or the
    # "txt" DKIM default is never injected onto the wire.
    return to_wire_exclude_unset(DomainCreate, data)


def _update_body(
    *,
    click_tracking: bool | None,
    open_tracking: bool | None,
    tracking: str | None | NotGiven,
    return_path: str | None,
    dkim_mode: str | None,
    inbound_enabled: bool | None,
) -> dict[str, Any]:
    data: dict[str, Any] = {}
    settings = _settings(click_tracking, open_tracking)
    if settings:
        data["settings"] = settings
    # NOT_GIVEN leaves tracking unchanged; None removes it (emits tracking: null);
    # a string sets the tracking name.
    if not isinstance(tracking, NotGiven):
        data["tracking"] = None if tracking is None else {"name": tracking}
    if return_path is not None:
        data["return_path"] = {"name": return_path}
    if dkim_mode is not None:
        data["dkim"] = {"mode": dkim_mode}
    if inbound_enabled is not None:
        data["inbound"] = {"enabled": inbound_enabled}
    return to_wire_exclude_unset(DomainUpdate, data)


def _settings(click_tracking: bool | None, open_tracking: bool | None) -> dict[str, Any]:
    settings: dict[str, Any] = {}
    if click_tracking is not None:
        settings["click_tracking"] = click_tracking
    if open_tracking is not None:
        settings["open_tracking"] = open_tracking
    return settings


class Domains:
    """Manage the workspace's sending domains. Reach it via ``client.domains``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def create(
        self,
        *,
        domain: str,
        return_path: str | None = None,
        tracking: str | None = None,
        dkim_mode: str | None = None,
        click_tracking: bool | None = None,
        open_tracking: bool | None = None,
        options: RequestOptions | None = None,
    ) -> Domain:
        """Register a sending domain. It returns in ``pending`` with the DNS
        records to publish; call :meth:`verify` once they are in place.

        ```python
        domain = client.domains.create(domain="mail.acme.com")
        print(domain.id, domain.status)
        ```
        """
        body = _create_body(
            domain=domain, return_path=return_path, tracking=tracking,
            dkim_mode=dkim_mode, click_tracking=click_tracking, open_tracking=open_tracking,
        )
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return Domain.model_validate(response.json())

    def get(self, domain_id: str, *, options: RequestOptions | None = None) -> Domain:
        """Fetch a single sending domain by id, with its DNS records and their
        per-record verification state.

        ```python
        domain = client.domains.get("dom_01krdgeqcxet5s7t44vh8rt9mg")
        print(domain.domain)
        ```
        """
        response = self._client.request("GET", f"{_PATH}/{domain_id}", **_opts(options))
        return Domain.model_validate(response.json())

    def update(
        self,
        domain_id: str,
        *,
        click_tracking: bool | None = None,
        open_tracking: bool | None = None,
        tracking: str | None | NotGiven = NOT_GIVEN,
        return_path: str | None = None,
        dkim_mode: str | None = None,
        inbound_enabled: bool | None = None,
        options: RequestOptions | None = None,
    ) -> Domain:
        """Update a sending domain. Only the fields you pass change; ``settings``
        apply immediately, while return-path/tracking/DKIM changes are staged
        until their new DNS records verify. Pass ``tracking=None`` to remove the
        tracking domain.

        ```python
        domain = client.domains.update(
            "dom_01krdgeqcxet5s7t44vh8rt9mg",
            click_tracking=True, open_tracking=True, tracking="links",
        )
        print(domain.id)
        ```
        """
        body = _update_body(
            click_tracking=click_tracking, open_tracking=open_tracking, tracking=tracking,
            return_path=return_path, dkim_mode=dkim_mode, inbound_enabled=inbound_enabled,
        )
        response = self._client.request("PATCH", f"{_PATH}/{domain_id}", body=body, **_opts(options))
        return Domain.model_validate(response.json())

    def delete(self, domain_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete a sending domain. Mail already accepted still sends; no new mail
        can be sent from it.

        ```python
        client.domains.delete("dom_01krdgeqcxet5s7t44vh8rt9mg")
        ```
        """
        self._client.request("DELETE", f"{_PATH}/{domain_id}", **_opts(options))

    def verify(self, domain_id: str, *, options: RequestOptions | None = None) -> Domain:
        """Trigger a fresh DNS check and return the refreshed domain with
        per-record results. Safe to repeat while waiting for DNS to propagate.

        ```python
        domain = client.domains.verify("dom_01krdgeqcxet5s7t44vh8rt9mg")
        print(domain.status)
        ```
        """
        response = self._client.request("POST", f"{_PATH}/{domain_id}/verify", **_opts(options))
        return Domain.model_validate(response.json())

    def list(
        self,
        *,
        name: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Domain]:
        """List the workspace's sending domains, newest first; iterate the page to
        auto-paginate.

        ```python
        for domain in client.domains.list():
            print(domain.id, domain.status)
        ```
        """
        query = _list_query({
            "name": name, "limit": limit,
            "starting_after": starting_after, "ending_before": ending_before,
        })
        return SyncPage(self._client, _PATH, query, Domain, options)


class AsyncDomains:
    """Async mirror of `Domains`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        domain: str,
        return_path: str | None = None,
        tracking: str | None = None,
        dkim_mode: str | None = None,
        click_tracking: bool | None = None,
        open_tracking: bool | None = None,
        options: RequestOptions | None = None,
    ) -> Domain:
        """Register a sending domain. It returns in ``pending`` with the DNS
        records to publish; call :meth:`verify` once they are in place."""
        body = _create_body(
            domain=domain, return_path=return_path, tracking=tracking,
            dkim_mode=dkim_mode, click_tracking=click_tracking, open_tracking=open_tracking,
        )
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return Domain.model_validate(response.json())

    async def get(self, domain_id: str, *, options: RequestOptions | None = None) -> Domain:
        """Fetch a single sending domain by id, with its DNS records."""
        response = await self._client.request("GET", f"{_PATH}/{domain_id}", **_opts(options))
        return Domain.model_validate(response.json())

    async def update(
        self,
        domain_id: str,
        *,
        click_tracking: bool | None = None,
        open_tracking: bool | None = None,
        tracking: str | None | NotGiven = NOT_GIVEN,
        return_path: str | None = None,
        dkim_mode: str | None = None,
        inbound_enabled: bool | None = None,
        options: RequestOptions | None = None,
    ) -> Domain:
        """Update a sending domain. Only the fields you pass change. Pass
        ``tracking=None`` to remove the tracking domain."""
        body = _update_body(
            click_tracking=click_tracking, open_tracking=open_tracking, tracking=tracking,
            return_path=return_path, dkim_mode=dkim_mode, inbound_enabled=inbound_enabled,
        )
        response = await self._client.request("PATCH", f"{_PATH}/{domain_id}", body=body, **_opts(options))
        return Domain.model_validate(response.json())

    async def delete(self, domain_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete a sending domain. Mail already accepted still sends."""
        await self._client.request("DELETE", f"{_PATH}/{domain_id}", **_opts(options))

    async def verify(self, domain_id: str, *, options: RequestOptions | None = None) -> Domain:
        """Trigger a fresh DNS check and return the refreshed domain. Safe to
        repeat while waiting for DNS to propagate."""
        response = await self._client.request("POST", f"{_PATH}/{domain_id}/verify", **_opts(options))
        return Domain.model_validate(response.json())

    def list(
        self,
        *,
        name: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Domain]:
        """List the workspace's sending domains, newest first; ``async for`` over
        the page to auto-paginate."""
        query = _list_query({
            "name": name, "limit": limit,
            "starting_after": starting_after, "ending_before": ending_before,
        })
        return AsyncPage(self._client, _PATH, query, Domain, options)
