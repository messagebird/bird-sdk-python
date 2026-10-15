"""Versions and language content under an Apple Messages template."""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.amb_templates_versions_gen import (
    AsyncAmbTemplatesVersionsBase,
    AmbTemplatesVersionsBase,
)
from bird.resources.amb_templates_versions_languages_gen import (
    AsyncAmbTemplatesVersionsLanguages,
    AmbTemplatesVersionsLanguages,
)


class AmbTemplatesVersions(AmbTemplatesVersionsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.languages = AmbTemplatesVersionsLanguages(client)


class AsyncAmbTemplatesVersions(AsyncAmbTemplatesVersionsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.languages = AsyncAmbTemplatesVersionsLanguages(client)
