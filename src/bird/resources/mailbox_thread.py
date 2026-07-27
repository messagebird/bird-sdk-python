"""Mailbox threads: ``client.mailbox_thread`` — list, inspect, and update email
conversation threads, plus read individual messages, their bodies, replies, and
attachments.

Reach thread messages via ``client.mailbox_thread.messages``.
"""

from __future__ import annotations

from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import (
    EmailThread,
    EmailThreadMessage,
    EmailThreadMessageAttachmentList,
    EmailThreadMessageBody,
    EmailThreadMessageReplyRequest,
    EmailThreadUpdateRequest,
)
from bird._models import to_wire_exclude_unset
from bird._types import RequestOptions
from bird.pagination import AsyncPage, SyncPage

_THREADS_PATH = "/v1/email/threads"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _update_body(**kwargs: Any) -> dict[str, Any]:
    # exclude_unset: omitted kwargs don't overwrite existing values (partial-update semantics).
    return to_wire_exclude_unset(EmailThreadUpdateRequest, kwargs)


def _reply_body(**kwargs: Any) -> dict[str, Any]:
    return to_wire_exclude_unset(EmailThreadMessageReplyRequest, kwargs)


class MailboxThreadMessages:
    """Read and reply to messages within a thread. Reach it via
    ``client.mailbox_thread.messages``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def list(
        self,
        thread_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        include: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[EmailThreadMessage]:
        """List messages in a thread, oldest first; iterate the page to
        auto-paginate. Pass ``include="extracted_text"`` to include stripped text.

        ```python
        for message in client.mailbox_thread_message.list("thr_01krdgeqcxet5s7t44vh8rt9mg"):
            print(message.id, message.subject)
        ```
        """
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            "include": include,
        })
        return SyncPage(
            self._client,
            f"{_THREADS_PATH}/{thread_id}/messages",
            query,
            EmailThreadMessage,
            options,
        )

    def get(
        self,
        thread_id: str,
        message_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> EmailThreadMessage:
        """Fetch a single message by id.

        ```python
        message = client.mailbox_thread_message.get(
            "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
        )
        print(message.subject)
        ```
        """
        response = self._client.request(
            "GET",
            f"{_THREADS_PATH}/{thread_id}/messages/{message_id}",
            **_opts(options),
        )
        return EmailThreadMessage.model_validate(response.json())

    def body(
        self,
        thread_id: str,
        message_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> EmailThreadMessageBody:
        """Fetch the full body (HTML and/or plain text) of a message.

        ```python
        body = client.mailbox_thread_message.body(
            "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
        )
        print(body.html)
        ```
        """
        response = self._client.request(
            "GET",
            f"{_THREADS_PATH}/{thread_id}/messages/{message_id}/body",
            **_opts(options),
        )
        return EmailThreadMessageBody.model_validate(response.json())

    def reply(
        self,
        thread_id: str,
        message_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThreadMessage:
        """Send a reply to a specific message in a thread.

        ```python
        reply = client.mailbox_thread_message.reply(
            "thr_01krdgeqcxet5s7t44vh8rt9mg",
            "msg_01krdgeqcxet5s7t44vh8rt9mg",
            text="Thanks for reaching out!",
        )
        print(reply.id)
        ```
        """
        body = _reply_body(**kwargs)
        response = self._client.request(
            "POST",
            f"{_THREADS_PATH}/{thread_id}/messages/{message_id}/reply",
            body=body,
            **_opts(options),
        )
        return EmailThreadMessage.model_validate(response.json())

    def attachments(
        self,
        thread_id: str,
        message_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> EmailThreadMessageAttachmentList:
        """List the attachments on a message.

        ```python
        result = client.mailbox_thread_message.attachments(
            "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
        )
        for attachment in result.data:
            print(attachment.filename, attachment.size)
        ```
        """
        response = self._client.request(
            "GET",
            f"{_THREADS_PATH}/{thread_id}/messages/{message_id}/attachments",
            **_opts(options),
        )
        return EmailThreadMessageAttachmentList.model_validate(response.json())


class MailboxThreads:
    """Manage email conversation threads. Reach it via ``client.mailbox_thread``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client
        self.messages = MailboxThreadMessages(client)

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> SyncPage[EmailThread]:
        """List email threads across the workspace, newest first; iterate the
        page to auto-paginate.

        ```python
        for thread in client.mailbox_thread.list():
            print(thread.id, thread.subject)
        ```
        """
        query = _list_query({
            "limit": limit,
            "starting_after": starting_after,
            "ending_before": ending_before,
            **kwargs,
        })
        return SyncPage(self._client, _THREADS_PATH, query, EmailThread, options)

    def get(self, thread_id: str, *, options: RequestOptions | None = None) -> EmailThread:
        """Fetch a single thread by id.

        ```python
        thread = client.mailbox_thread.get("thr_01krdgeqcxet5s7t44vh8rt9mg")
        print(thread.subject)
        ```
        """
        response = self._client.request("GET", f"{_THREADS_PATH}/{thread_id}", **_opts(options))
        return EmailThread.model_validate(response.json())

    def update(
        self,
        thread_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThread:
        """Update a thread's mutable fields (e.g. labels, contact link).
        Only the fields you pass change.

        ```python
        thread = client.mailbox_thread.update(
            "thr_01krdgeqcxet5s7t44vh8rt9mg",
            labels={"add": ["archive"]},
        )
        print(thread.id)
        ```
        """
        body = _update_body(**kwargs)
        response = self._client.request(
            "PATCH", f"{_THREADS_PATH}/{thread_id}", body=body, **_opts(options)
        )
        return EmailThread.model_validate(response.json())

    def delete(
        self,
        thread_id: str,
        *,
        permanent: bool = False,
        options: RequestOptions | None = None,
    ) -> None:
        """Soft-delete a thread (purged after 30 days). Pass ``permanent=True`` to skip the restore window.

        ```python
        client.mailbox_thread.delete("thr_01krdgeqcxet5s7t44vh8rt9mg")
        ```
        """
        opts = _opts(options)
        if permanent:
            opts["extra_query"] = {**opts.get("extra_query", {}), "permanent": "true"}
        self._client.request("DELETE", f"{_THREADS_PATH}/{thread_id}", **opts)


class AsyncMailboxThreadMessages:
    """Async mirror of `MailboxThreadMessages`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    def list(
        self,
        thread_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        include: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[EmailThreadMessage]:
        """List messages in a thread, oldest first; ``async for`` over the page
        to auto-paginate."""
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            "include": include,
        })
        return AsyncPage(
            self._client,
            f"{_THREADS_PATH}/{thread_id}/messages",
            query,
            EmailThreadMessage,
            options,
        )

    async def get(
        self,
        thread_id: str,
        message_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> EmailThreadMessage:
        """Fetch a single message by id."""
        response = await self._client.request(
            "GET",
            f"{_THREADS_PATH}/{thread_id}/messages/{message_id}",
            **_opts(options),
        )
        return EmailThreadMessage.model_validate(response.json())

    async def body(
        self,
        thread_id: str,
        message_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> EmailThreadMessageBody:
        """Fetch the full body (HTML and/or plain text) of a message."""
        response = await self._client.request(
            "GET",
            f"{_THREADS_PATH}/{thread_id}/messages/{message_id}/body",
            **_opts(options),
        )
        return EmailThreadMessageBody.model_validate(response.json())

    async def reply(
        self,
        thread_id: str,
        message_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThreadMessage:
        """Send a reply to a specific message in a thread."""
        body = _reply_body(**kwargs)
        response = await self._client.request(
            "POST",
            f"{_THREADS_PATH}/{thread_id}/messages/{message_id}/reply",
            body=body,
            **_opts(options),
        )
        return EmailThreadMessage.model_validate(response.json())

    async def attachments(
        self,
        thread_id: str,
        message_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> EmailThreadMessageAttachmentList:
        """List the attachments on a message."""
        response = await self._client.request(
            "GET",
            f"{_THREADS_PATH}/{thread_id}/messages/{message_id}/attachments",
            **_opts(options),
        )
        return EmailThreadMessageAttachmentList.model_validate(response.json())


class AsyncMailboxThreads:
    """Async mirror of `MailboxThreads`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client
        self.messages = AsyncMailboxThreadMessages(client)

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> AsyncPage[EmailThread]:
        """List email threads across the workspace, newest first; ``async for``
        over the page to auto-paginate."""
        query = _list_query({
            "limit": limit,
            "starting_after": starting_after,
            "ending_before": ending_before,
            **kwargs,
        })
        return AsyncPage(self._client, _THREADS_PATH, query, EmailThread, options)

    async def get(self, thread_id: str, *, options: RequestOptions | None = None) -> EmailThread:
        """Fetch a single thread by id."""
        response = await self._client.request(
            "GET", f"{_THREADS_PATH}/{thread_id}", **_opts(options)
        )
        return EmailThread.model_validate(response.json())

    async def update(
        self,
        thread_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThread:
        """Update a thread's mutable fields. Only the fields you pass change."""
        body = _update_body(**kwargs)
        response = await self._client.request(
            "PATCH", f"{_THREADS_PATH}/{thread_id}", body=body, **_opts(options)
        )
        return EmailThread.model_validate(response.json())

    async def delete(self, thread_id: str, *, permanent: bool = False, options: RequestOptions | None = None) -> None:
        """Soft-delete a thread (purged after 30 days). Pass ``permanent=True`` to skip the restore window."""
        opts = _opts(options)
        if permanent:
            opts["extra_query"] = {**opts.get("extra_query", {}), "permanent": "true"}
        await self._client.request("DELETE", f"{_THREADS_PATH}/{thread_id}", **opts)
