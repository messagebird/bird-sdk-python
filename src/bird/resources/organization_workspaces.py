"""``client.organization.workspaces`` — the organization's workspaces.

The generated base carries the workspace operations; this wrapper exists to nest
the multi-partner solution number connect, reached at
``client.organization.workspaces.whatsapp_numbers``.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.organization_workspaces_gen import (
    AsyncOrganizationWorkspacesBase,
    OrganizationWorkspacesBase,
)
from bird.resources.organization_workspaces_whatsapp_numbers_gen import (
    AsyncOrganizationWorkspacesWhatsappNumbers,
    OrganizationWorkspacesWhatsappNumbers,
)


class OrganizationWorkspaces(OrganizationWorkspacesBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.whatsapp_numbers = OrganizationWorkspacesWhatsappNumbers(client)


class AsyncOrganizationWorkspaces(AsyncOrganizationWorkspacesBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.whatsapp_numbers = AsyncOrganizationWorkspacesWhatsappNumbers(client)
