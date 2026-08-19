"""The WhatsApp channel: ``client.whatsapp`` — send a message, read one back,
list the message log, and list a single message's event timeline.

A send carries exactly one kind of content: a template, or free-form ``text``,
``image``, ``video``, ``audio``, ``sticker``, ``document`` or ``location``.
Free-form content is deliverable only inside an open 24-hour customer service
window.
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
    from_: str | None = None,
    template: str | None = None,
    language: str | None = None,
    components: Sequence[Mapping[str, Any]] | None = None,
    text: Mapping[str, Any] | None = None,
    image: Mapping[str, Any] | None = None,
    video: Mapping[str, Any] | None = None,
    audio: Mapping[str, Any] | None = None,
    sticker: Mapping[str, Any] | None = None,
    document: Mapping[str, Any] | None = None,
    location: Mapping[str, Any] | None = None,
    tags: Sequence[Mapping[str, str]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"to": to}
    if from_ is not None:
        body["from"] = from_
    if template is not None:
        # A wat_-prefixed value is the id; anything else is the slug handle.
        tmpl: dict[str, Any] = {"id" if template.startswith("wat_") else "slug": template}
        if language is not None:
            tmpl["language"] = language
        if components is not None:
            tmpl["components"] = components
        body["template"] = tmpl
    content: dict[str, Mapping[str, Any] | None] = {
        "text": text,
        "image": image,
        "video": video,
        "audio": audio,
        "sticker": sticker,
        "document": document,
        "location": location,
    }
    for name, value in content.items():
        if value is not None:
            body[name] = value
    if tags is not None:
        body["tags"] = tags
    if metadata is not None:
        body["metadata"] = metadata
    return body


class Whatsapp(WhatsappBase):
    """Send and read WhatsApp messages. Reach it via ``client.whatsapp``."""

    def send(
        self,
        *,
        to: str,
        from_: str | None = None,
        template: str | None = None,
        language: str | None = None,
        components: Sequence[Mapping[str, Any]] | None = None,
        text: Mapping[str, Any] | None = None,
        image: Mapping[str, Any] | None = None,
        video: Mapping[str, Any] | None = None,
        audio: Mapping[str, Any] | None = None,
        sticker: Mapping[str, Any] | None = None,
        document: Mapping[str, Any] | None = None,
        location: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> WhatsAppMessage:
        """Send one message to a single recipient, carrying exactly one kind of
        content: a template named by its id (``wat_…``) or slug, or a free-form
        arm shaped like its wire object (``text={"body": …}``). Every send but a
        Bird-managed template needs ``from_``. The result is ``accepted``, not
        yet delivered — read it back with ``get`` or follow its timeline with
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
        body = _send_body(
            to=to,
            from_=from_,
            template=template,
            language=language,
            components=components,
            text=text,
            image=image,
            video=video,
            audio=audio,
            sticker=sticker,
            document=document,
            location=location,
            tags=tags,
            metadata=metadata,
        )
        return self._write("POST", _PATH, body, WhatsAppMessage, options)


class AsyncWhatsapp(AsyncWhatsappBase):
    """Async mirror of `Whatsapp`: ``await`` each call, ``async for`` over a list."""

    async def send(
        self,
        *,
        to: str,
        from_: str | None = None,
        template: str | None = None,
        language: str | None = None,
        components: Sequence[Mapping[str, Any]] | None = None,
        text: Mapping[str, Any] | None = None,
        image: Mapping[str, Any] | None = None,
        video: Mapping[str, Any] | None = None,
        audio: Mapping[str, Any] | None = None,
        sticker: Mapping[str, Any] | None = None,
        document: Mapping[str, Any] | None = None,
        location: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> WhatsAppMessage:
        """Send one WhatsApp message to a single recipient."""
        body = _send_body(
            to=to,
            from_=from_,
            template=template,
            language=language,
            components=components,
            text=text,
            image=image,
            video=video,
            audio=audio,
            sticker=sticker,
            document=document,
            location=location,
            tags=tags,
            metadata=metadata,
        )
        return await self._write("POST", _PATH, body, WhatsAppMessage, options)
