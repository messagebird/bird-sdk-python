"""Workspace contacts: ``client.contacts`` — create/get/update/delete a contact,
list the workspace's contacts, and bulk upsert with ``batch``.

A contact is unique by email address within a workspace, and optionally by your
own ``external_id``. ``batch`` matches each entry by email, creating or updating
up to 1,000 contacts in one request and optionally adding them all to one or
more audiences.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import (
    Contact,
    ContactCreateRequest,
    ContactUpdateRequest,
    ContactUpsertRequest,
    ContactUpsertResult,
)
from bird._models import to_wire
from bird._types import RequestOptions
from bird.pagination import AsyncPage, SyncPage

_PATH = "/v1/contacts"
_BATCH_PATH = "/v1/contacts/batch"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _create_body(
    *,
    email: str,
    first_name: str | None,
    last_name: str | None,
    external_id: str | None,
    data: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return to_wire(ContactCreateRequest, {
        "email":       email,
        "first_name":  first_name,
        "last_name":   last_name,
        "external_id": external_id,
        "data":        data,
    })


def _update_body(
    *,
    email: str | None,
    first_name: str | None,
    last_name: str | None,
    external_id: str | None,
    data: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return to_wire(ContactUpdateRequest, {
        "email":       email,
        "first_name":  first_name,
        "last_name":   last_name,
        "external_id": external_id,
        "data":        data,
    })


def _batch_body(
    *,
    contacts: Sequence[Mapping[str, Any]],
    audience_ids: Sequence[str] | None,
    data_mode: str | None,
) -> dict[str, Any]:
    # `data_mode` defaults to "merge" on the generated model, so an unset value must
    # be passed through as an explicit None (not omitted) or exclude_none would never
    # see it and the default would leak onto the wire.
    return to_wire(ContactUpsertRequest, {
        "contacts":     list(contacts),
        "audience_ids": audience_ids,
        "data_mode":    data_mode,
    })


class Contacts:
    """Manage workspace contacts. Reach it via ``client.contacts``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def create(
        self,
        *,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        external_id: str | None = None,
        data: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Contact:
        """Create a contact by email address. Fails with a conflict if the email or
        ``external_id`` is already used by another contact in the workspace.

        ```python
        contact = client.contacts.create(email="jane@acme.com", first_name="Jane")
        print(contact.id, contact.email)
        ```
        """
        body = _create_body(
            email=email, first_name=first_name, last_name=last_name,
            external_id=external_id, data=data,
        )
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return Contact.model_validate(response.json())

    def get(self, contact_id: str, *, options: RequestOptions | None = None) -> Contact:
        """Fetch a single contact by id.

        ```python
        contact = client.contacts.get("con_01krdgeqcxet5s7t44vh8rt9mg")
        print(contact.email)
        ```
        """
        response = self._client.request("GET", f"{_PATH}/{contact_id}", **_opts(options))
        return Contact.model_validate(response.json())

    def update(
        self,
        contact_id: str,
        *,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        external_id: str | None = None,
        data: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Contact:
        """Edit a contact. Only the fields you pass change; ``data`` is merged into
        the contact's existing custom values, and a key set to ``None`` removes it.

        ```python
        contact = client.contacts.update("con_01krdgeqcxet5s7t44vh8rt9mg", first_name="Jane")
        print(contact.first_name)
        ```
        """
        body = _update_body(
            email=email, first_name=first_name, last_name=last_name,
            external_id=external_id, data=data,
        )
        response = self._client.request("PATCH", f"{_PATH}/{contact_id}", body=body, **_opts(options))
        return Contact.model_validate(response.json())

    def delete(self, contact_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete a contact and remove it from every audience it belongs to.
        Suppression records for the address are unaffected.

        ```python
        client.contacts.delete("con_01krdgeqcxet5s7t44vh8rt9mg")
        ```
        """
        self._client.request("DELETE", f"{_PATH}/{contact_id}", **_opts(options))

    def batch(
        self,
        *,
        contacts: Sequence[Mapping[str, Any]],
        audience_ids: Sequence[str] | None = None,
        data_mode: str | None = None,
        options: RequestOptions | None = None,
    ) -> ContactUpsertResult:
        """Create or update up to 1,000 contacts in one request, matched by email
        address. Each item is shaped like the keyword arguments of :meth:`create`.
        A failed entry does not abort the rest of the request — check
        ``result.data[i].status``.

        ```python
        result = client.contacts.batch(contacts=[{"email": "jane@acme.com", "first_name": "Jane"}])
        for item in result.data:
            print(item.email, item.status)
        ```
        """
        body = _batch_body(contacts=contacts, audience_ids=audience_ids, data_mode=data_mode)
        response = self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return ContactUpsertResult.model_validate(response.json())

    def list(
        self,
        *,
        email: str | None = None,
        external_id: str | None = None,
        q: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Contact]:
        """List contacts, newest first; iterate the page to auto-paginate. Look one
        up by exact ``email`` or ``external_id``, or search by email substring.

        ```python
        for contact in client.contacts.list(q="acme.com"):
            print(contact.id, contact.email)
        ```
        """
        query = _list_query({
            "email": email, "external_id": external_id, "q": q,
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return SyncPage(self._client, _PATH, query, Contact, options)


class AsyncContacts:
    """Async mirror of `Contacts`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        external_id: str | None = None,
        data: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Contact:
        """Create a contact by email address."""
        body = _create_body(
            email=email, first_name=first_name, last_name=last_name,
            external_id=external_id, data=data,
        )
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return Contact.model_validate(response.json())

    async def get(self, contact_id: str, *, options: RequestOptions | None = None) -> Contact:
        """Fetch a single contact by id."""
        response = await self._client.request("GET", f"{_PATH}/{contact_id}", **_opts(options))
        return Contact.model_validate(response.json())

    async def update(
        self,
        contact_id: str,
        *,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        external_id: str | None = None,
        data: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> Contact:
        """Edit a contact. Only the fields you pass change."""
        body = _update_body(
            email=email, first_name=first_name, last_name=last_name,
            external_id=external_id, data=data,
        )
        response = await self._client.request(
            "PATCH", f"{_PATH}/{contact_id}", body=body, **_opts(options)
        )
        return Contact.model_validate(response.json())

    async def delete(self, contact_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete a contact and remove it from every audience it belongs to."""
        await self._client.request("DELETE", f"{_PATH}/{contact_id}", **_opts(options))

    async def batch(
        self,
        *,
        contacts: Sequence[Mapping[str, Any]],
        audience_ids: Sequence[str] | None = None,
        data_mode: str | None = None,
        options: RequestOptions | None = None,
    ) -> ContactUpsertResult:
        """Create or update up to 1,000 contacts in one request, matched by email
        address."""
        body = _batch_body(contacts=contacts, audience_ids=audience_ids, data_mode=data_mode)
        response = await self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return ContactUpsertResult.model_validate(response.json())

    def list(
        self,
        *,
        email: str | None = None,
        external_id: str | None = None,
        q: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Contact]:
        """List contacts, newest first; ``async for`` over the page to auto-paginate."""
        query = _list_query({
            "email": email, "external_id": external_id, "q": q,
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return AsyncPage(self._client, _PATH, query, Contact, options)
