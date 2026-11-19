from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_seeding_address_gen import AsyncEmailSeedingAddress, EmailSeedingAddress
from bird.resources.email_seeding_runs_gen import AsyncEmailSeedingRuns, EmailSeedingRuns
from bird.resources.email_seeding_settings_gen import AsyncEmailSeedingSettings, EmailSeedingSettings
from bird.resources.email_seeding_sources_gen import AsyncEmailSeedingSources, EmailSeedingSources


class EmailSeeding:
    def __init__(self, client: SyncAPIClient) -> None:
        self.settings = EmailSeedingSettings(client)
        self.address = EmailSeedingAddress(client)
        self.runs = EmailSeedingRuns(client)
        self.sources = EmailSeedingSources(client)


class AsyncEmailSeeding:
    def __init__(self, client: AsyncAPIClient) -> None:
        self.settings = AsyncEmailSeedingSettings(client)
        self.address = AsyncEmailSeedingAddress(client)
        self.runs = AsyncEmailSeedingRuns(client)
        self.sources = AsyncEmailSeedingSources(client)
