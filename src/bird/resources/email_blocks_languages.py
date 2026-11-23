"""Block languages: ``client.email.blocks.languages`` — the generated language
facade plus its nested ``revisions`` collection, which a generated class can't
declare.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_blocks_languages_gen import AsyncEmailBlocksLanguagesBase
from bird.resources.email_blocks_languages_gen import EmailBlocksLanguagesBase
from bird.resources.email_blocks_languages_revisions_gen import (
    AsyncEmailBlocksLanguagesRevisions,
    EmailBlocksLanguagesRevisions,
)


class EmailBlocksLanguages(EmailBlocksLanguagesBase):
    """A block's per-language drafts. Reach it via ``client.email.blocks.languages``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.revisions = EmailBlocksLanguagesRevisions(client)


class AsyncEmailBlocksLanguages(AsyncEmailBlocksLanguagesBase):
    """Async mirror of `EmailBlocksLanguages`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.revisions = AsyncEmailBlocksLanguagesRevisions(client)
