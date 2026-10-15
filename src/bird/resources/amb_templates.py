"""Apple Messages template identities, versions, and language content."""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.amb_templates_gen import AsyncAmbTemplatesBase, AmbTemplatesBase
from bird.resources.amb_templates_versions import (
    AsyncAmbTemplatesVersions,
    AmbTemplatesVersions,
)


class AmbTemplates(AmbTemplatesBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.versions = AmbTemplatesVersions(client)


class AsyncAmbTemplates(AsyncAmbTemplatesBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.versions = AsyncAmbTemplatesVersions(client)
