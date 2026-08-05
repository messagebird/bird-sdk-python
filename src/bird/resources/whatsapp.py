"""The WhatsApp channel: ``client.whatsapp`` — send a template message, read a
message back, list the message log, and list a single message's event timeline.

Templates are currently the only supported content type, so every send must
include one; free-text content will be added in a future release. Bird selects
the sender number from the template's category, so there is no sender field
on a send.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._generated import WhatsAppMessage
from bird._types import RequestOptions
from bird.resources.whatsapp_gen import AsyncWhatsappBase, WhatsappBase

_PATH = "/v1/whatsapp/messages"


def _send_body(
    *,
    to: str,
    template: str | None = None,
    language: str | None = None,
    components: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"to": to}
    if template is not None:
        # A wat_-prefixed value is the id; anything else is the slug handle.
        tmpl: dict[str, Any] = {"id" if template.startswith("wat_") else "slug": template}
        if language is not None:
            tmpl["language"] = language
        if components is not None:
            tmpl["components"] = components
        body["template"] = tmpl
    return body


class Whatsapp(WhatsappBase):
    """Send and read WhatsApp messages. Reach it via ``client.whatsapp``."""

    def send(
        self,
        *,
        to: str,
        template: str | None = None,
        language: str | None = None,
        components: Sequence[Mapping[str, Any]] | None = None,
        options: RequestOptions | None = None,
    ) -> WhatsAppMessage:
        """Send a template message to a single recipient, naming the template
        by its id (``wat_…``) or its slug. The result is ``accepted``, not yet
        delivered — read it back with ``get`` or follow its timeline with
        ``list_events``.

        ```python
        msg = client.whatsapp.send(
            to="+31612345678",
            template="bird_otp",
            language="en",
            components=[{"type": "body", "parameters": [{"type": "text", "text": "123456"}]}],
        )
        print(msg.id, msg.status)
        ```
        """
        body = _send_body(to=to, template=template, language=language, components=components)
        return self._write("POST", _PATH, body, WhatsAppMessage, options)


class AsyncWhatsapp(AsyncWhatsappBase):
    """Async mirror of `Whatsapp`: ``await`` each call, ``async for`` over a list."""

    async def send(
        self,
        *,
        to: str,
        template: str | None = None,
        language: str | None = None,
        components: Sequence[Mapping[str, Any]] | None = None,
        options: RequestOptions | None = None,
    ) -> WhatsAppMessage:
        """Send a template message to a single recipient."""
        body = _send_body(to=to, template=template, language=language, components=components)
        return await self._write("POST", _PATH, body, WhatsAppMessage, options)
