from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.voice_ring_groups_gen import (
    AsyncVoiceRingGroupsBase,
    VoiceRingGroupsBase,
)
from bird.resources.voice_ring_groups_members_gen import (
    AsyncVoiceRingGroupsMembers,
    VoiceRingGroupsMembers,
)


class VoiceRingGroups(VoiceRingGroupsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.members = VoiceRingGroupsMembers(client)


class AsyncVoiceRingGroups(AsyncVoiceRingGroupsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.members = AsyncVoiceRingGroupsMembers(client)
