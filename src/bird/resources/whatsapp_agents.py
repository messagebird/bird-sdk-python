"""``client.whatsapp.agents`` — the WhatsApp Business Agent on one of your numbers.

The agent itself is onboarded in the dashboard; this namespace carries what is
public about it, the notifications at ``client.whatsapp.agents.notifications``.
"""

from __future__ import annotations

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._resource import AsyncResource, Resource
from bird.resources.whatsapp_agents_notifications_gen import (
    AsyncWhatsappAgentsNotifications,
    WhatsappAgentsNotifications,
)


class WhatsappAgents(Resource):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.notifications = WhatsappAgentsNotifications(client)


class AsyncWhatsappAgents(AsyncResource):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.notifications = AsyncWhatsappAgentsNotifications(client)
