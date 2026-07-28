"""Custom contact properties: ``client.contact_properties`` — define typed custom
fields that become available in contact ``data`` and as broadcast template
variables, and archive/unarchive them.

A property is unique by ``key`` within a workspace; the key and ``type`` are
immutable once created — archive it and create a new one instead of changing
either.
"""

from __future__ import annotations

from typing import Any

from bird._generated import (
    ContactProperty,
    ContactPropertyCreateRequest,
    ContactPropertyUpdateRequest,
)
from bird._models import to_wire
from bird._types import RequestOptions
from bird.resources.contact_properties_gen import (
    AsyncContactPropertiesBase,
    ContactPropertiesBase,
)

_PATH = "/v1/contact-properties"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _create_body(*, key: str, type: str, fallback_value: Any | None) -> dict[str, Any]:
    return to_wire(
        ContactPropertyCreateRequest,
        {"key": key, "type": type, "fallback_value": fallback_value},
    )


def _update_body(*, fallback_value: Any | None) -> dict[str, Any]:
    return to_wire(ContactPropertyUpdateRequest, {"fallback_value": fallback_value})


class ContactProperties(ContactPropertiesBase):
    """Manage the workspace's custom contact properties. Reach it via
    ``client.contact_properties``."""

    def create(
        self,
        *,
        key: str,
        type: str,
        fallback_value: Any | None = None,
        options: RequestOptions | None = None,
    ) -> ContactProperty:
        """Define a custom property (``key`` + value ``type``) that contacts in the
        workspace can carry. Keys are unique within the workspace; the key and
        ``type`` cannot be changed after creation.

        ```python
        prop = client.contact_properties.create(key="plan", type="string")
        print(prop.id, prop.key)
        ```
        """
        body = _create_body(key=key, type=type, fallback_value=fallback_value)
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
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
        response = self._client.request(
            "PATCH", f"{_PATH}/{property_id}", body=body, **_opts(options)
        )
        return ContactProperty.model_validate(response.json())


class AsyncContactProperties(AsyncContactPropertiesBase):
    """Async mirror of `ContactProperties`: ``await`` each call, ``async for`` over
    a list."""

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
