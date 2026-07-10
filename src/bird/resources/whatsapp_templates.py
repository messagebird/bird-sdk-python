"""Workspace WhatsApp templates: ``client.whatsapp_templates`` — list the
message templates available to the workspace.

The catalogue is read-only through this SDK.
"""

from __future__ import annotations

from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import WhatsAppTemplateList
from bird._types import RequestOptions

_PATH = "/v1/whatsapp/templates"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


class WhatsappTemplates:
    """Read workspace WhatsApp templates. Reach it via ``client.whatsapp_templates``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def list(self, *, options: RequestOptions | None = None) -> WhatsAppTemplateList:
        """List the message templates available to the workspace. Not
        paginated — the full catalogue is returned in ``.data``.

        ```python
        templates = client.whatsapp_templates.list()
        for template in templates.data:
            print(template.name, template.status)
        ```
        """
        response = self._client.request("GET", _PATH, **_opts(options))
        return WhatsAppTemplateList.model_validate(response.json())


class AsyncWhatsappTemplates:
    """Async mirror of `WhatsappTemplates`: ``await`` each call."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def list(self, *, options: RequestOptions | None = None) -> WhatsAppTemplateList:
        """List the message templates available to the workspace. Not
        paginated — the full catalogue is returned in ``.data``."""
        response = await self._client.request("GET", _PATH, **_opts(options))
        return WhatsAppTemplateList.model_validate(response.json())
