"""Custom contact properties: ``client.contact_properties`` — define typed custom
fields that become available in contact ``data`` and as broadcast template
variables, and archive/unarchive them.

A property is unique by ``key`` within a workspace; the key and ``type`` are
immutable once created — archive it and create a new one instead of changing
either.
"""

from __future__ import annotations

from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import ContactProperty, ContactPropertyCreateRequest, ContactPropertyUpdateRequest
from bird._models import to_wire
from bird._types import RequestOptions
from bird.pagination import AsyncPage, SyncPage

_PATH = "/v1/contact-properties"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _create_body(*, key: str, type: str, fallback_value: Any | None) -> dict[str, Any]:
    return to_wire(
        ContactPropertyCreateRequest, {"key": key, "type": type, "fallback_value": fallback_value}
    )


def _update_body(*, fallback_value: Any | None) -> dict[str, Any]:
    return to_wire(ContactPropertyUpdateRequest, {"fallback_value": fallback_value})


class ContactProperties:
    """Manage the workspace's custom contact properties. Reach it via
    ``client.contact_properties``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def create(
        self,
        *,
        key: str,
        type: str,
        fallback_value: Any | None = None,
        options: RequestOptions | None = None,
    ) -> ContactProperty:
        """Define a custom property (``key`` + value ``type``) that contacts in the
        workspace can carry. The key becomes available in contact ``data`` and as a
        template variable in broadcasts. Keys are unique within the workspace; the
        key and ``type`` cannot be changed after creation.

        ```python
        prop = client.contact_properties.create(key="plan", type="string")
        print(prop.id, prop.key)
        ```
        """
        body = _create_body(key=key, type=type, fallback_value=fallback_value)
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return ContactProperty.model_validate(response.json())

    def get(self, property_id: str, *, options: RequestOptions | None = None) -> ContactProperty:
        """Fetch a single contact property by id.

        ```python
        prop = client.contact_properties.get("prp_01krdgeqcxet5s7t44vh8rt9mg")
        print(prop.key)
        ```
        """
        response = self._client.request("GET", f"{_PATH}/{property_id}", **_opts(options))
        return ContactProperty.model_validate(response.json())

    def update(
        self,
        property_id: str,
        *,
        fallback_value: Any | None = None,
        options: RequestOptions | None = None,
    ) -> ContactProperty:
        """Update a contact property's fallback value. The key and type are
        immutable — create a new property instead.

        ```python
        prop = client.contact_properties.update("prp_01krdgeqcxet5s7t44vh8rt9mg", fallback_value="free")
        print(prop.fallback_value)
        ```
        """
        body = _update_body(fallback_value=fallback_value)
        response = self._client.request("PATCH", f"{_PATH}/{property_id}", body=body, **_opts(options))
        return ContactProperty.model_validate(response.json())

    def archive(self, property_id: str, *, options: RequestOptions | None = None) -> ContactProperty:
        """Archive a contact property. The key stops being accepted in new contact
        writes and stops rendering in templates; every value already stored on a
        contact is preserved. Reverse it with :meth:`unarchive`.

        ```python
        prop = client.contact_properties.archive("prp_01krdgeqcxet5s7t44vh8rt9mg")
        print(prop.archived)
        ```
        """
        response = self._client.request("POST", f"{_PATH}/{property_id}/archive", **_opts(options))
        return ContactProperty.model_validate(response.json())

    def unarchive(self, property_id: str, *, options: RequestOptions | None = None) -> ContactProperty:
        """Reactivate an archived contact property. The key is accepted in contact
        writes and renders in templates again; stored values were never removed.

        ```python
        prop = client.contact_properties.unarchive("prp_01krdgeqcxet5s7t44vh8rt9mg")
        print(prop.archived)
        ```
        """
        response = self._client.request("POST", f"{_PATH}/{property_id}/unarchive", **_opts(options))
        return ContactProperty.model_validate(response.json())

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[ContactProperty]:
        """List the workspace's contact properties; iterate the page to
        auto-paginate.

        ```python
        for prop in client.contact_properties.list():
            print(prop.id, prop.key)
        ```
        """
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return SyncPage(self._client, _PATH, query, ContactProperty, options)


class AsyncContactProperties:
    """Async mirror of `ContactProperties`: ``await`` each call, ``async for`` over
    a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        key: str,
        type: str,
        fallback_value: Any | None = None,
        options: RequestOptions | None = None,
    ) -> ContactProperty:
        """Define a custom property (``key`` + value ``type``) that contacts in the
        workspace can carry."""
        body = _create_body(key=key, type=type, fallback_value=fallback_value)
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return ContactProperty.model_validate(response.json())

    async def get(self, property_id: str, *, options: RequestOptions | None = None) -> ContactProperty:
        """Fetch a single contact property by id."""
        response = await self._client.request("GET", f"{_PATH}/{property_id}", **_opts(options))
        return ContactProperty.model_validate(response.json())

    async def update(
        self,
        property_id: str,
        *,
        fallback_value: Any | None = None,
        options: RequestOptions | None = None,
    ) -> ContactProperty:
        """Update a contact property's fallback value. The key and type are
        immutable."""
        body = _update_body(fallback_value=fallback_value)
        response = await self._client.request(
            "PATCH", f"{_PATH}/{property_id}", body=body, **_opts(options)
        )
        return ContactProperty.model_validate(response.json())

    async def archive(self, property_id: str, *, options: RequestOptions | None = None) -> ContactProperty:
        """Archive a contact property. Every value already stored on a contact is
        preserved. Reverse it with :meth:`unarchive`."""
        response = await self._client.request(
            "POST", f"{_PATH}/{property_id}/archive", **_opts(options)
        )
        return ContactProperty.model_validate(response.json())

    async def unarchive(
        self, property_id: str, *, options: RequestOptions | None = None
    ) -> ContactProperty:
        """Reactivate an archived contact property. Stored values were never
        removed."""
        response = await self._client.request(
            "POST", f"{_PATH}/{property_id}/unarchive", **_opts(options)
        )
        return ContactProperty.model_validate(response.json())

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[ContactProperty]:
        """List the workspace's contact properties; ``async for`` over the page to
        auto-paginate."""
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return AsyncPage(self._client, _PATH, query, ContactProperty, options)
