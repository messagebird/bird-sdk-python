from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.voice_legs_gen import AsyncVoiceLegsBase, VoiceLegsBase
from bird.resources.voice_legs_recordings import AsyncVoiceLegsRecordings, VoiceLegsRecordings


class VoiceLegs(VoiceLegsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.recordings = VoiceLegsRecordings(client)


class AsyncVoiceLegs(AsyncVoiceLegsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.recordings = AsyncVoiceLegsRecordings(client)
