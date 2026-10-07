from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.email_inbox_insights_seed_tests_gen import AsyncEmailInboxInsightsSeedTestsBase, EmailInboxInsightsSeedTestsBase
from bird.resources.email_inbox_insights_seed_tests_configuration_gen import AsyncEmailInboxInsightsSeedTestsConfiguration, EmailInboxInsightsSeedTestsConfiguration


class EmailInboxInsightsSeedTests(EmailInboxInsightsSeedTestsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.configuration = EmailInboxInsightsSeedTestsConfiguration(client)


class AsyncEmailInboxInsightsSeedTests(AsyncEmailInboxInsightsSeedTestsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.configuration = AsyncEmailInboxInsightsSeedTestsConfiguration(client)
