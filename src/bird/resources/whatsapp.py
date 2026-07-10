"""The WhatsApp channel: ``client.whatsapp`` — send a template message, read a
message back, list the message log, and list a single message's event
timeline.

Templates are currently the only supported content type, so every send must
include one; free-text content will be added in a future release. Bird selects
the sender number from the template's category, so there is no sender field
on a send.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import WhatsAppEventList, WhatsAppMessage
from bird._types import RequestOptions
from bird.pagination import AsyncPage, SyncPage

_PATH = "/v1/whatsapp/messages"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _events_opts(options: RequestOptions | None, type: str | None) -> dict[str, Any]:
    # Fold the filter into extra_query; a caller-supplied extra_query wins on a clash.
    opts = _opts(options)
    if type is not None:
        opts["extra_query"] = {"type": type, **opts.get("extra_query", {})}
    return opts


def _send_body(
    *,
    to: str,
    template: str | None = None,
    language: str | None = None,
    components: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"to": to}
    if template is not None:
        tmpl: dict[str, Any] = {"name": template}
        if language is not None:
            tmpl["language"] = language
        if components is not None:
            tmpl["components"] = components
        body["template"] = tmpl
    return body


class Whatsapp:
    """Send and read WhatsApp messages. Reach it via ``client.whatsapp``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def send(
        self,
        *,
        to: str,
        template: str | None = None,
        language: str | None = None,
        components: Sequence[Mapping[str, Any]] | None = None,
        options: RequestOptions | None = None,
    ) -> WhatsAppMessage:
        """Send a template message to a single recipient. The result is
        ``accepted``, not yet delivered — read it back with ``get`` or follow
        its timeline with ``list_events``.

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
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return WhatsAppMessage.model_validate(response.json())

    def get(self, message_id: str, *, options: RequestOptions | None = None) -> WhatsAppMessage:
        """Fetch a single WhatsApp message with its current delivery status and
        failure detail if applicable."""
        response = self._client.request("GET", f"{_PATH}/{message_id}", **_opts(options))
        return WhatsAppMessage.model_validate(response.json())

    def list(
        self,
        *,
        status: Sequence[str] | None = None,
        phone_number: str | None = None,
        bsuid: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[WhatsAppMessage]:
        """List WhatsApp messages, newest first; iterate the page to auto-paginate.

        ```python
        for message in client.whatsapp.list(status=["delivered"]):
            print(message.id, message.status)
        ```
        """
        query = _list_query({
            "status": status, "phone_number": phone_number, "bsuid": bsuid,
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            "created_after": created_after, "created_before": created_before,
        })
        return SyncPage(self._client, _PATH, query, WhatsAppMessage, options)

    def list_events(
        self, message_id: str, *, type: str | None = None, options: RequestOptions | None = None
    ) -> WhatsAppEventList:
        """List the lifecycle event timeline for a single WhatsApp message, in
        chronological order. The timeline is bounded and returned in full —
        this list is not paginated.

        ```python
        events = client.whatsapp.list_events("wam_01krdgeqcxet5s7t44vh8rt9mg")
        for event in events.data:
            print(event.type, event.occurred_at)
        ```
        """
        response = self._client.request(
            "GET", f"{_PATH}/{message_id}/events", **_events_opts(options, type)
        )
        return WhatsAppEventList.model_validate(response.json())


class AsyncWhatsapp:
    """Async mirror of `Whatsapp`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

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
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return WhatsAppMessage.model_validate(response.json())

    async def get(self, message_id: str, *, options: RequestOptions | None = None) -> WhatsAppMessage:
        """Fetch a single WhatsApp message with its current delivery status and
        failure detail if applicable."""
        response = await self._client.request("GET", f"{_PATH}/{message_id}", **_opts(options))
        return WhatsAppMessage.model_validate(response.json())

    def list(
        self,
        *,
        status: Sequence[str] | None = None,
        phone_number: str | None = None,
        bsuid: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[WhatsAppMessage]:
        """List WhatsApp messages, newest first; ``async for`` over the page to auto-paginate."""
        query = _list_query({
            "status": status, "phone_number": phone_number, "bsuid": bsuid,
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            "created_after": created_after, "created_before": created_before,
        })
        return AsyncPage(self._client, _PATH, query, WhatsAppMessage, options)

    async def list_events(
        self, message_id: str, *, type: str | None = None, options: RequestOptions | None = None
    ) -> WhatsAppEventList:
        """List the lifecycle event timeline for a single WhatsApp message, in
        chronological order. Not paginated — the full timeline is returned in
        ``.data``."""
        response = await self._client.request(
            "GET", f"{_PATH}/{message_id}/events", **_events_opts(options, type)
        )
        return WhatsAppEventList.model_validate(response.json())
