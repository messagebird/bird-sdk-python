"""Mailboxes: ``client.mailbox`` — create and manage email mailboxes, compose
outbound messages, inspect labels, and configure per-mailbox receive rules.

Reach receive rules via ``client.mailbox.receive_rules``.
"""

from __future__ import annotations

from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import (
    EmailMailboxComposeRequest,
    EmailMailboxLabelList,
    EmailThreadMessage,
    Mailbox,
    MailboxCreate,
    MailboxStatsResponse,
    MailboxUpdate,
    ReceiveRule,
    ReceiveRuleCreate,
)
from bird._models import to_wire, to_wire_exclude_unset
from bird._types import RequestOptions
from bird.pagination import AsyncPage, SyncPage

_PATH = "/v1/email/mailboxes"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _create_body(**kwargs: Any) -> dict[str, Any]:
    return to_wire_exclude_unset(MailboxCreate, kwargs)


def _update_body(**kwargs: Any) -> dict[str, Any]:
    return to_wire_exclude_unset(MailboxUpdate, kwargs)


def _compose_body(**kwargs: Any) -> dict[str, Any]:
    return to_wire_exclude_unset(EmailMailboxComposeRequest, kwargs)


def _receive_rule_create_body(**kwargs: Any) -> dict[str, Any]:
    return to_wire(ReceiveRuleCreate, kwargs)


class MailboxReceiveRules:
    """Manage receive rules for a mailbox. Reach it via ``client.mailbox.receive_rules``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def list(
        self,
        mailbox_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[ReceiveRule]:
        """List the receive rules configured for a mailbox; iterate the page to
        auto-paginate.

        ```python
        for rule in client.mailbox_receive_rule.list("mbx_01krdgeqcxet5s7t44vh8rt9mg"):
            print(rule.id, rule.action)
        ```
        """
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return SyncPage(
            self._client,
            f"{_PATH}/{mailbox_id}/receive-rules",
            query,
            ReceiveRule,
            options,
        )

    def create(
        self,
        mailbox_id: str,
        *,
        action: str,
        entry: str,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> ReceiveRule:
        """Create a receive rule on a mailbox. Block rules always win; to flip
        an entry's action, delete the existing rule and re-create it.

        ```python
        rule = client.mailbox_receive_rule.create(
            "mbx_01krdgeqcxet5s7t44vh8rt9mg", action="block", entry="spam.example.com",
        )
        print(rule.id)
        ```
        """
        body = _receive_rule_create_body(action=action, entry=entry, **kwargs)
        response = self._client.request(
            "POST", f"{_PATH}/{mailbox_id}/receive-rules", body=body, **_opts(options)
        )
        return ReceiveRule.model_validate(response.json())

    def delete(
        self, mailbox_id: str, rule_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Delete a receive rule from a mailbox.

        ```python
        client.mailbox_receive_rule.delete(
            "mbx_01krdgeqcxet5s7t44vh8rt9mg", "rrule_01krdgeqcxet5s7t44vh8rt9mg",
        )
        ```
        """
        self._client.request(
            "DELETE", f"{_PATH}/{mailbox_id}/receive-rules/{rule_id}", **_opts(options)
        )


class Mailboxes:
    """Manage the workspace's email mailboxes. Reach it via ``client.mailbox``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client
        self.receive_rules = MailboxReceiveRules(client)

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> SyncPage[Mailbox]:
        """List the workspace's mailboxes, newest first; iterate the page to
        auto-paginate.

        ```python
        for mailbox in client.mailbox.list():
            print(mailbox.id, mailbox.address)
        ```
        """
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            **kwargs,
        })
        return SyncPage(self._client, _PATH, query, Mailbox, options)

    def create(
        self,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> Mailbox:
        """Create a new mailbox in the workspace. All fields are optional; omit
        ``local_part`` to have Bird generate a random handle on inbox.ai.

        ```python
        mailbox = client.mailbox.create(display_name="Acme Support")
        print(mailbox.id)
        ```
        """
        body = _create_body(**kwargs)
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return Mailbox.model_validate(response.json())

    def get(self, mailbox_id: str, *, options: RequestOptions | None = None) -> Mailbox:
        """Fetch a single mailbox by id.

        ```python
        mailbox = client.mailbox.get("mbx_01krdgeqcxet5s7t44vh8rt9mg")
        print(mailbox.address)
        ```
        """
        response = self._client.request("GET", f"{_PATH}/{mailbox_id}", **_opts(options))
        return Mailbox.model_validate(response.json())

    def update(
        self,
        mailbox_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> Mailbox:
        """Edit a mailbox. Only the fields you pass change.

        ```python
        mailbox = client.mailbox.update("mbx_01krdgeqcxet5s7t44vh8rt9mg", display_name="Billing")
        print(mailbox.display_name)
        ```
        """
        body = _update_body(**kwargs)
        response = self._client.request("PATCH", f"{_PATH}/{mailbox_id}", body=body, **_opts(options))
        return Mailbox.model_validate(response.json())

    def delete(self, mailbox_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete a mailbox and all its threads. Soft-deletes the mailbox (purged after 30 days). Pass permanent=True to skip the restore window.

        ```python
        client.mailbox.delete("mbx_01krdgeqcxet5s7t44vh8rt9mg")
        ```
        """
        self._client.request("DELETE", f"{_PATH}/{mailbox_id}", **_opts(options))

    def restore(self, mailbox_id: str, *, options: RequestOptions | None = None) -> Mailbox:
        """Restore a previously deleted mailbox.

        ```python
        mailbox = client.mailbox.restore("mbx_01krdgeqcxet5s7t44vh8rt9mg")
        print(mailbox.id)
        ```
        """
        response = self._client.request(
            "POST", f"{_PATH}/{mailbox_id}/restore", **_opts(options)
        )
        return Mailbox.model_validate(response.json())

    def resume(self, mailbox_id: str, *, options: RequestOptions | None = None) -> Mailbox:
        """Resume a paused mailbox.

        ```python
        mailbox = client.mailbox.resume("mbx_01krdgeqcxet5s7t44vh8rt9mg")
        print(mailbox.id)
        ```
        """
        response = self._client.request(
            "POST", f"{_PATH}/{mailbox_id}/resume", **_opts(options)
        )
        return Mailbox.model_validate(response.json())

    def stats(
        self,
        mailbox_id: str,
        *,
        from_: str | None = None,
        to: str | None = None,
        granularity: str | None = None,
        timezone: str | None = None,
        options: RequestOptions | None = None,
    ) -> MailboxStatsResponse:
        """Retrieve delivery statistics for a mailbox.

        Pass from_, to, granularity, timezone to bound the window.
        from_ maps to the from query parameter (reserved word in Python).

        ```python
        stats = client.mailbox.stats("mbx_01krdgeqcxet5s7t44vh8rt9mg")
        print(stats.summary)
        ```
        """
        query = _list_query({"from": from_, "to": to, "granularity": granularity, "timezone": timezone})
        response = self._client.request(
            "GET", f"{_PATH}/{mailbox_id}/stats", extra_query=query or None, **_opts(options)
        )
        return MailboxStatsResponse.model_validate(response.json())

    def compose(
        self,
        mailbox_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThreadMessage:
        """Compose and send an outbound message from a mailbox.

        ```python
        msg = client.mailbox.compose(
            "mbx_01krdgeqcxet5s7t44vh8rt9mg",
            to=[{"address": "user@example.com"}],
            subject="Hello",
            text="Hi there",
        )
        print(msg.id, msg.thread_id)
        ```
        """
        body = _compose_body(**kwargs)
        response = self._client.request(
            "POST", f"{_PATH}/{mailbox_id}/messages", body=body, **_opts(options)
        )
        return EmailThreadMessage.model_validate(response.json())

    def labels(self, mailbox_id: str, *, options: RequestOptions | None = None) -> EmailMailboxLabelList:
        """List the labels available on a mailbox.

        ```python
        labels = client.mailbox.labels("mbx_01krdgeqcxet5s7t44vh8rt9mg")
        for label in labels.data:
            print(label.name)
        ```
        """
        response = self._client.request(
            "GET", f"{_PATH}/{mailbox_id}/labels", **_opts(options)
        )
        return EmailMailboxLabelList.model_validate(response.json())


class AsyncMailboxReceiveRules:
    """Async mirror of `MailboxReceiveRules`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    def list(
        self,
        mailbox_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[ReceiveRule]:
        """List the receive rules configured for a mailbox; ``async for`` over
        the page to auto-paginate."""
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return AsyncPage(
            self._client,
            f"{_PATH}/{mailbox_id}/receive-rules",
            query,
            ReceiveRule,
            options,
        )

    async def create(
        self,
        mailbox_id: str,
        *,
        action: str,
        entry: str,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> ReceiveRule:
        """Create a receive rule on a mailbox."""
        body = _receive_rule_create_body(action=action, entry=entry, **kwargs)
        response = await self._client.request(
            "POST", f"{_PATH}/{mailbox_id}/receive-rules", body=body, **_opts(options)
        )
        return ReceiveRule.model_validate(response.json())

    async def delete(
        self, mailbox_id: str, rule_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Delete a receive rule from a mailbox."""
        await self._client.request(
            "DELETE", f"{_PATH}/{mailbox_id}/receive-rules/{rule_id}", **_opts(options)
        )


class AsyncMailboxes:
    """Async mirror of `Mailboxes`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client
        self.receive_rules = AsyncMailboxReceiveRules(client)

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> AsyncPage[Mailbox]:
        """List the workspace's mailboxes, newest first; ``async for`` over the
        page to auto-paginate."""
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            **kwargs,
        })
        return AsyncPage(self._client, _PATH, query, Mailbox, options)

    async def create(
        self,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> Mailbox:
        """Create a new mailbox in the workspace."""
        body = _create_body(**kwargs)
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return Mailbox.model_validate(response.json())

    async def get(self, mailbox_id: str, *, options: RequestOptions | None = None) -> Mailbox:
        """Fetch a single mailbox by id."""
        response = await self._client.request("GET", f"{_PATH}/{mailbox_id}", **_opts(options))
        return Mailbox.model_validate(response.json())

    async def update(
        self,
        mailbox_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> Mailbox:
        """Edit a mailbox. Only the fields you pass change."""
        body = _update_body(**kwargs)
        response = await self._client.request(
            "PATCH", f"{_PATH}/{mailbox_id}", body=body, **_opts(options)
        )
        return Mailbox.model_validate(response.json())

    async def delete(self, mailbox_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete a mailbox and all its threads. Soft-deletes the mailbox (purged after 30 days). Pass permanent=True to skip the restore window."""
        await self._client.request("DELETE", f"{_PATH}/{mailbox_id}", **_opts(options))

    async def restore(self, mailbox_id: str, *, options: RequestOptions | None = None) -> Mailbox:
        """Restore a previously deleted mailbox."""
        response = await self._client.request(
            "POST", f"{_PATH}/{mailbox_id}/restore", **_opts(options)
        )
        return Mailbox.model_validate(response.json())

    async def resume(self, mailbox_id: str, *, options: RequestOptions | None = None) -> Mailbox:
        """Resume a paused mailbox."""
        response = await self._client.request(
            "POST", f"{_PATH}/{mailbox_id}/resume", **_opts(options)
        )
        return Mailbox.model_validate(response.json())

    async def stats(
        self,
        mailbox_id: str,
        *,
        from_: str | None = None,
        to: str | None = None,
        granularity: str | None = None,
        timezone: str | None = None,
        options: RequestOptions | None = None,
    ) -> MailboxStatsResponse:
        """Retrieve delivery statistics for a mailbox."""
        query = _list_query({"from": from_, "to": to, "granularity": granularity, "timezone": timezone})
        response = await self._client.request(
            "GET", f"{_PATH}/{mailbox_id}/stats", extra_query=query or None, **_opts(options)
        )
        return MailboxStatsResponse.model_validate(response.json())

    async def compose(
        self,
        mailbox_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThreadMessage:
        """Compose and send an outbound message from a mailbox."""
        body = _compose_body(**kwargs)
        response = await self._client.request(
            "POST", f"{_PATH}/{mailbox_id}/messages", body=body, **_opts(options)
        )
        return EmailThreadMessage.model_validate(response.json())

    async def labels(
        self, mailbox_id: str, *, options: RequestOptions | None = None
    ) -> EmailMailboxLabelList:
        """List the labels available on a mailbox."""
        response = await self._client.request(
            "GET", f"{_PATH}/{mailbox_id}/labels", **_opts(options)
        )
        return EmailMailboxLabelList.model_validate(response.json())
