from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.voice_calls_gen import AsyncVoiceCalls, VoiceCalls
from bird.resources.voice_legs_gen import AsyncVoiceLegs, VoiceLegs


class Voice:
    def __init__(self, client: SyncAPIClient) -> None:
        self.legs = VoiceLegs(client)
        self.calls = VoiceCalls(client)


class AsyncVoice:
    def __init__(self, client: AsyncAPIClient) -> None:
        self.legs = AsyncVoiceLegs(client)
        self.calls = AsyncVoiceCalls(client)
