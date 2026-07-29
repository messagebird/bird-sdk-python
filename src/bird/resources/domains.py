"""Domains: ``client.domains`` — register and manage sending domains via the API.

Register a domain, publish the DNS records it returns, then call :meth:`verify`
until it is usable as a sender. ``return_path`` and ``tracking`` are the name
part only — Bird appends the sending domain (``links`` on ``mail.acme.com``
becomes ``links.mail.acme.com``).

``create`` and ``update`` are hand-written: they flatten the nested
tracking/return-path/dkim/settings wire objects into flat keyword arguments.
The read, delete, and verify methods are generated onto the base.
"""

from __future__ import annotations

from typing import Any

from bird._generated import Domain, DomainCreate, DomainUpdate
from bird._models import to_wire_exclude_unset
from bird._types import Omit, RequestOptions, omit
from bird.resources.domains_gen import AsyncDomainsBase, DomainsBase

_PATH = "/v1/email/domains"


def _settings(click_tracking: bool | None, open_tracking: bool | None) -> dict[str, Any]:
    settings: dict[str, Any] = {}
    if click_tracking is not None:
        settings["click_tracking"] = click_tracking
    if open_tracking is not None:
        settings["open_tracking"] = open_tracking
    return settings


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
    tracking: str | None | Omit,
    return_path: str | None,
    dkim_mode: str | None,
    inbound_enabled: bool | None,
) -> dict[str, Any]:
    data: dict[str, Any] = {}
    settings = _settings(click_tracking, open_tracking)
    if settings:
        data["settings"] = settings
    # omit leaves tracking unchanged; None removes it (emits tracking: null);
    # a string sets the tracking name.
    if not isinstance(tracking, Omit):
        data["tracking"] = None if tracking is None else {"name": tracking}
    if return_path is not None:
        data["return_path"] = {"name": return_path}
    if dkim_mode is not None:
        data["dkim"] = {"mode": dkim_mode}
    if inbound_enabled is not None:
        data["inbound"] = {"enabled": inbound_enabled}
    return to_wire_exclude_unset(DomainUpdate, data)


class Domains(DomainsBase):
    """Manage the workspace's sending domains. Reach it via ``client.domains``."""

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
        return self._write("POST", _PATH, body, Domain, options)

    def update(
        self,
        domain_id: str,
        *,
        click_tracking: bool | None = None,
        open_tracking: bool | None = None,
        tracking: str | None | Omit = omit,
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
        return self._write("PATCH", f"{_PATH}/{domain_id}", body, Domain, options)


class AsyncDomains(AsyncDomainsBase):
    """Async mirror of `Domains`: ``await`` each call, ``async for`` over a list."""

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
        return await self._write("POST", _PATH, body, Domain, options)

    async def update(
        self,
        domain_id: str,
        *,
        click_tracking: bool | None = None,
        open_tracking: bool | None = None,
        tracking: str | None | Omit = omit,
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
        return await self._write("PATCH", f"{_PATH}/{domain_id}", body, Domain, options)
