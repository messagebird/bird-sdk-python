"""Nested mailbox resources share their parent client and request lifecycle."""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._types import EmailDefaults
from bird.resources.email_mailboxes_forwarding_address_gen import (
    AsyncEmailMailboxesForwardingAddress,
    EmailMailboxesForwardingAddress,
)
from bird.resources.email_mailboxes_gen import AsyncEmailMailboxesBase
from bird.resources.email_mailboxes_gen import EmailMailboxesBase
from bird.resources.email_mailboxes_messages import (
    AsyncEmailMailboxesMessages,
    EmailMailboxesMessages,
)
from bird.resources.email_mailboxes_receive_rules_gen import (
    AsyncEmailMailboxesReceiveRules,
    EmailMailboxesReceiveRules,
)
from bird.resources.email_mailboxes_scheduled_messages_gen import (
    AsyncEmailMailboxesScheduledMessages,
    EmailMailboxesScheduledMessages,
)


class EmailMailboxes(EmailMailboxesBase):
    """Manage the workspace's mailboxes. Reach it via ``client.email.mailboxes``."""

    def __init__(self, client: SyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self.forwarding_address = EmailMailboxesForwardingAddress(client)
        self.messages = EmailMailboxesMessages(client, defaults)
        self.scheduled_messages = EmailMailboxesScheduledMessages(client)
        self.receive_rules = EmailMailboxesReceiveRules(client)


class AsyncEmailMailboxes(AsyncEmailMailboxesBase):
    """Async mirror of `EmailMailboxes`."""

    def __init__(self, client: AsyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self.forwarding_address = AsyncEmailMailboxesForwardingAddress(client)
        self.messages = AsyncEmailMailboxesMessages(client, defaults)
        self.scheduled_messages = AsyncEmailMailboxesScheduledMessages(client)
        self.receive_rules = AsyncEmailMailboxesReceiveRules(client)
