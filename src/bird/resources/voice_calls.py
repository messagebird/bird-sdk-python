from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.voice_calls_gen import AsyncVoiceCallsBase, VoiceCallsBase
from bird.resources.voice_calls_recordings_gen import (
    AsyncVoiceCallsRecordings,
    VoiceCallsRecordings,
)


class VoiceCalls(VoiceCallsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.recordings = VoiceCallsRecordings(client)


class AsyncVoiceCalls(AsyncVoiceCallsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.recordings = AsyncVoiceCallsRecordings(client)
