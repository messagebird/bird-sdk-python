from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.organization_workspaces_gen import (
    AsyncOrganizationWorkspaces,
    OrganizationWorkspaces,
)


class OrganizationResource:
    def __init__(self, client: SyncAPIClient) -> None:
        self.workspaces = OrganizationWorkspaces(client)


class AsyncOrganizationResource:
    def __init__(self, client: AsyncAPIClient) -> None:
        self.workspaces = AsyncOrganizationWorkspaces(client)
