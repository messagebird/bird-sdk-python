"""The Realtime channel: ``client.realtime`` — the generated publish facade plus
its nested ``channels`` and ``members`` collections, which a generated class can't
declare.

Every Realtime operation is scoped to one Realtime app and authenticated with that
app's own credentials, sent as the ``X-Realtime-Key``/``X-Realtime-Secret`` headers
alongside the workspace bearer token. Configure them once on the client
(``Bird(realtime_key=..., realtime_secret=...)``); a call made without them raises
``BirdError`` before any request is sent.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.realtime_channels_gen import (
    AsyncRealtimeChannels,
    RealtimeChannels,
)
from bird.resources.realtime_gen import AsyncRealtimeBase, RealtimeBase
from bird.resources.realtime_members_gen import (
    AsyncRealtimeMembers,
    RealtimeMembers,
)


class Realtime(RealtimeBase):
    """Publish to a Realtime app and inspect its live state. Reach it via ``client.realtime``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.channels = RealtimeChannels(client)
        self.members = RealtimeMembers(client)


class AsyncRealtime(AsyncRealtimeBase):
    """Async mirror of `Realtime`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.channels = AsyncRealtimeChannels(client)
        self.members = AsyncRealtimeMembers(client)
