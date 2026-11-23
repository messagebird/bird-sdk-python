"""Blocks: ``client.email.blocks`` — the generated block facade plus its nested
``languages`` collection, which a generated class can't declare.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_blocks_gen import AsyncEmailBlocksBase
from bird.resources.email_blocks_gen import EmailBlocksBase
from bird.resources.email_blocks_languages import (
    AsyncEmailBlocksLanguages,
    EmailBlocksLanguages,
)


class EmailBlocks(EmailBlocksBase):
    """Reusable sections templates link. Reach it via ``client.email.blocks``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.languages = EmailBlocksLanguages(client)


class AsyncEmailBlocks(AsyncEmailBlocksBase):
    """Async mirror of `EmailBlocks`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.languages = AsyncEmailBlocksLanguages(client)
