"""Audiences: ``client.audiences`` — group contacts into a named, static list you
manage via the API, plus the membership operations on it (list/add/remove).

An audience starts empty; add contacts with ``add_contacts`` or a contact
``batch`` upsert (``audience_ids``). ``dynamic`` and ``external`` audience
types are preview values and currently unavailable.
"""

from __future__ import annotations

from typing import Any, Sequence

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import (
    Audience,
    AudienceContactsAddRequest,
    AudienceContactsRemoveRequest,
    AudienceCreateRequest,
    AudienceMember,
    AudienceUpdateRequest,
)
from bird._models import to_wire
from bird._types import RequestOptions
from bird.pagination import AsyncPage, SyncPage

_PATH = "/v1/audiences"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _create_body(*, name: str, description: str | None, type: str | None) -> dict[str, Any]:
    # `type` defaults to "static" on the generated model, so an unset value must be
    # passed through as an explicit None (not omitted) or exclude_none would never
    # see it and the default would leak onto the wire.
    return to_wire(AudienceCreateRequest, {"name": name, "description": description, "type": type})


def _update_body(*, name: str | None, description: str | None) -> dict[str, Any]:
    return to_wire(AudienceUpdateRequest, {"name": name, "description": description})


def _add_contacts_body(*, contact_ids: Sequence[str]) -> dict[str, Any]:
    return to_wire(AudienceContactsAddRequest, {"contact_ids": list(contact_ids)})


def _remove_contacts_body(*, contact_ids: Sequence[str]) -> dict[str, Any]:
    return to_wire(AudienceContactsRemoveRequest, {"contact_ids": list(contact_ids)})


class Audiences:
    """Manage the workspace's audiences. Reach it via ``client.audiences``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        type: str | None = None,
        options: RequestOptions | None = None,
    ) -> Audience:
        """Create an audience in the workspace. New audiences start empty — add
        contacts via :meth:`add_contacts` or a contact ``batch`` upsert.

        ```python
        audience = client.audiences.create(name="Newsletter subscribers")
        print(audience.id, audience.name)
        ```
        """
        body = _create_body(name=name, description=description, type=type)
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return Audience.model_validate(response.json())

    def get(self, audience_id: str, *, options: RequestOptions | None = None) -> Audience:
        """Fetch a single audience by id.

        ```python
        audience = client.audiences.get("adn_01krdgeqcxet5s7t44vh8rt9mg")
        print(audience.name)
        ```
        """
        response = self._client.request("GET", f"{_PATH}/{audience_id}", **_opts(options))
        return Audience.model_validate(response.json())

    def update(
        self,
        audience_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        options: RequestOptions | None = None,
    ) -> Audience:
        """Edit an audience's name or description. Only the fields you pass change.

        ```python
        audience = client.audiences.update("adn_01krdgeqcxet5s7t44vh8rt9mg", name="Renamed")
        print(audience.name)
        ```
        """
        body = _update_body(name=name, description=description)
        response = self._client.request("PATCH", f"{_PATH}/{audience_id}", body=body, **_opts(options))
        return Audience.model_validate(response.json())

    def delete(self, audience_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete an audience and its memberships. Contacts themselves are not
        deleted. Fails while a broadcast targeting the audience is scheduled,
        accepted, sending, or canceling.

        ```python
        client.audiences.delete("adn_01krdgeqcxet5s7t44vh8rt9mg")
        ```
        """
        self._client.request("DELETE", f"{_PATH}/{audience_id}", **_opts(options))

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Audience]:
        """List the workspace's audiences, newest first; iterate the page to
        auto-paginate.

        ```python
        for audience in client.audiences.list():
            print(audience.id, audience.name)
        ```
        """
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return SyncPage(self._client, _PATH, query, Audience, options)

    def list_contacts(
        self,
        audience_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[AudienceMember]:
        """List an audience's contacts, most recently joined first; iterate the
        page to auto-paginate. Each entry pairs the contact with the time it
        joined.

        ```python
        for member in client.audiences.list_contacts("adn_01krdgeqcxet5s7t44vh8rt9mg"):
            print(member.contact.email, member.joined_at)
        ```
        """
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return SyncPage(self._client, f"{_PATH}/{audience_id}/contacts", query, AudienceMember, options)

    def add_contacts(
        self,
        audience_id: str,
        *,
        contact_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> None:
        """Add up to 1,000 existing contacts to a static audience. A contact
        already a member is left in place; if any id does not exist, the whole
        request fails and no contacts are added.

        ```python
        client.audiences.add_contacts(
            "adn_01krdgeqcxet5s7t44vh8rt9mg", contact_ids=["con_01krdgeqcxet5s7t44vh8rt9mg"],
        )
        ```
        """
        body = _add_contacts_body(contact_ids=contact_ids)
        self._client.request("POST", f"{_PATH}/{audience_id}/contacts", body=body, **_opts(options))

    def remove_contacts(
        self,
        audience_id: str,
        *,
        contact_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> None:
        """Remove up to 1,000 contacts from a static audience. A contact that
        isn't a member is skipped; if any id does not exist, the whole request
        fails and no contacts are removed. The contacts themselves are not
        deleted.

        ```python
        client.audiences.remove_contacts(
            "adn_01krdgeqcxet5s7t44vh8rt9mg", contact_ids=["con_01krdgeqcxet5s7t44vh8rt9mg"],
        )
        ```
        """
        body = _remove_contacts_body(contact_ids=contact_ids)
        self._client.request(
            "POST", f"{_PATH}/{audience_id}/contacts/remove", body=body, **_opts(options)
        )

    def remove_contact(
        self, audience_id: str, contact_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Remove one contact's membership in an audience. The contact itself is
        not deleted and remains a member of any other audiences. Removing a
        contact that isn't a member succeeds with no effect.

        ```python
        client.audiences.remove_contact(
            "adn_01krdgeqcxet5s7t44vh8rt9mg", "con_01krdgeqcxet5s7t44vh8rt9mg",
        )
        ```
        """
        self._client.request(
            "DELETE", f"{_PATH}/{audience_id}/contacts/{contact_id}", **_opts(options)
        )


class AsyncAudiences:
    """Async mirror of `Audiences`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        type: str | None = None,
        options: RequestOptions | None = None,
    ) -> Audience:
        """Create an audience in the workspace. New audiences start empty."""
        body = _create_body(name=name, description=description, type=type)
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return Audience.model_validate(response.json())

    async def get(self, audience_id: str, *, options: RequestOptions | None = None) -> Audience:
        """Fetch a single audience by id."""
        response = await self._client.request("GET", f"{_PATH}/{audience_id}", **_opts(options))
        return Audience.model_validate(response.json())

    async def update(
        self,
        audience_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        options: RequestOptions | None = None,
    ) -> Audience:
        """Edit an audience's name or description. Only the fields you pass change."""
        body = _update_body(name=name, description=description)
        response = await self._client.request(
            "PATCH", f"{_PATH}/{audience_id}", body=body, **_opts(options)
        )
        return Audience.model_validate(response.json())

    async def delete(self, audience_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete an audience and its memberships. Contacts themselves are not
        deleted."""
        await self._client.request("DELETE", f"{_PATH}/{audience_id}", **_opts(options))

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Audience]:
        """List the workspace's audiences, newest first; ``async for`` over the
        page to auto-paginate."""
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return AsyncPage(self._client, _PATH, query, Audience, options)

    def list_contacts(
        self,
        audience_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[AudienceMember]:
        """List an audience's contacts, most recently joined first; ``async for``
        over the page to auto-paginate."""
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return AsyncPage(self._client, f"{_PATH}/{audience_id}/contacts", query, AudienceMember, options)

    async def add_contacts(
        self,
        audience_id: str,
        *,
        contact_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> None:
        """Add up to 1,000 existing contacts to a static audience."""
        body = _add_contacts_body(contact_ids=contact_ids)
        await self._client.request(
            "POST", f"{_PATH}/{audience_id}/contacts", body=body, **_opts(options)
        )

    async def remove_contacts(
        self,
        audience_id: str,
        *,
        contact_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> None:
        """Remove up to 1,000 contacts from a static audience."""
        body = _remove_contacts_body(contact_ids=contact_ids)
        await self._client.request(
            "POST", f"{_PATH}/{audience_id}/contacts/remove", body=body, **_opts(options)
        )

    async def remove_contact(
        self, audience_id: str, contact_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Remove one contact's membership in an audience. The contact itself is
        not deleted."""
        await self._client.request(
            "DELETE", f"{_PATH}/{audience_id}/contacts/{contact_id}", **_opts(options)
        )
