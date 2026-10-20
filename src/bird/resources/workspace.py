from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.workspace_gen import AsyncWorkspaceBase, WorkspaceBase
from bird.resources.workspace_quotas_gen import AsyncWorkspaceQuotas, WorkspaceQuotas


class WorkspaceResource(WorkspaceBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.quotas = WorkspaceQuotas(client)


class AsyncWorkspaceResource(AsyncWorkspaceBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.quotas = AsyncWorkspaceQuotas(client)
