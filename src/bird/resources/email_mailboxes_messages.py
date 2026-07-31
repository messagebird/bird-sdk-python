"""Mailbox messages: ``client.email.mailboxes.messages`` — the override residue
over the generated mailbox facade: ``create`` (address-list body).
"""

from __future__ import annotations

from typing import Any

from bird._generated import (
    EmailMailboxComposeRequest,
    EmailThreadMessage,
)
from bird._models import to_wire_exclude_unset
from bird._types import RequestOptions
from bird._resource import AsyncResource, Resource

_PATH = "/v1/email/mailboxes"


def _compose_body(**kwargs: Any) -> dict[str, Any]:
    return to_wire_exclude_unset(EmailMailboxComposeRequest, kwargs)


class EmailMailboxesMessages(Resource):
    """Send messages from a mailbox. Reach it via ``client.email.mailboxes.messages``."""

    def create(
        self,
        mailbox_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThreadMessage:
        """Compose and send an outbound message from a mailbox.

        ```python
        msg = client.email.mailboxes.messages.create(
            "mbx_01krdgeqcxet5s7t44vh8rt9mg",
            to=[{"address": "user@example.com"}],
            subject="Hello",
            text="Hi there",
        )
        print(msg.id, msg.thread_id)
        ```
        """
        return self._write(
            "POST",
            f"{_PATH}/{mailbox_id}/messages",
            _compose_body(**kwargs),
            EmailThreadMessage,
            options,
        )


class AsyncEmailMailboxesMessages(AsyncResource):
    """Async mirror of `EmailMailboxesMessages`."""

    async def create(
        self,
        mailbox_id: str,
        *,
        options: RequestOptions | None = None,
        **kwargs: Any,
    ) -> EmailThreadMessage:
        """Compose and send an outbound message from a mailbox."""
        return await self._write(
            "POST",
            f"{_PATH}/{mailbox_id}/messages",
            _compose_body(**kwargs),
            EmailThreadMessage,
            options,
        )
