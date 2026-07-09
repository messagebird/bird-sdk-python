"""The SMS channel: ``client.sms`` — send an SMS (free text or by stored
template), read a message back, and list the message log.

A send carries either ``text`` (with a ``category``) or a ``template`` (by id or
name, with its ``parameters``); the two are mutually exclusive.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import SMSMessage, SMSMessageBatchResponse
from bird._types import RequestOptions
from bird.pagination import AsyncPage, SyncPage

_PATH = "/v1/sms/messages"
_BATCH_PATH = "/v1/sms/batches"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _send_body(
    *,
    to: str,
    from_: str | None = None,
    text: str | None = None,
    category: str | None = None,
    template: str | None = None,
    language: str | None = None,
    parameters: Mapping[str, Any] | None = None,
    tags: Sequence[Mapping[str, str]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    # The generated send request is an anyOf(text | template) with no single
    # wrappable model, so the body is assembled as a plain dict here; unset fields
    # are dropped. ``from_`` maps to the wire field "from" (a Python keyword).
    body: dict[str, Any] = {
        "to": to,
        "from": from_,
        "text": text,
        "category": category,
        "tags": tags,
        "metadata": metadata,
    }
    if template is not None:
        # An smt_-prefixed value is the id; anything else is the name handle.
        tmpl: dict[str, Any] = {"id" if template.startswith("smt_") else "name": template}
        if language is not None:
            tmpl["language"] = language
        if parameters is not None:
            tmpl["parameters"] = parameters
        body["template"] = tmpl
    return {key: value for key, value in body.items() if value is not None}


def _message_body(m: Mapping[str, Any]) -> dict[str, Any]:
    return _send_body(
        to=m["to"],
        from_=m.get("from_"),
        text=m.get("text"),
        category=m.get("category"),
        template=m.get("template"),
        language=m.get("language"),
        parameters=m.get("parameters"),
        tags=m.get("tags"),
        metadata=m.get("metadata"),
    )


class Sms:
    """Send and read SMS messages. Reach it via ``client.sms``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def send(
        self,
        *,
        to: str,
        from_: str | None = None,
        text: str | None = None,
        category: str | None = None,
        template: str | None = None,
        language: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> SMSMessage:
        """Send one SMS to a single recipient. Supply either ``text`` (with a
        ``category``) or a stored ``template`` (by id or name, with ``parameters``).
        The result is ``accepted``, not yet delivered — read it back with ``get``.

        ```python
        msg = client.sms.send(
            to="+15551234567",
            text="Your verification code is 123456.",
            category="authentication",
        )
        print(msg.id, msg.status)
        ```

        ```python
        client.sms.send(
            to="+15551234567",
            template="bird_otp_verification",
            parameters={"code": "123456"},
        )
        ```
        """
        body = _send_body(
            to=to, from_=from_, text=text, category=category, template=template,
            language=language, parameters=parameters, tags=tags, metadata=metadata,
        )
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return SMSMessage.model_validate(response.json())

    def send_batch(
        self, *, messages: Sequence[Mapping[str, Any]], options: RequestOptions | None = None
    ) -> SMSMessageBatchResponse:
        """Send up to 100 independent SMS messages in one call. Each item is shaped
        like the keyword arguments of ``send``; all are validated before any queue."""
        body = [_message_body(m) for m in messages]
        response = self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return SMSMessageBatchResponse.model_validate(response.json())

    def get(self, message_id: str, *, options: RequestOptions | None = None) -> SMSMessage:
        """Fetch a single SMS message with its current status, segments, and cost."""
        response = self._client.request("GET", f"{_PATH}/{message_id}", **_opts(options))
        return SMSMessage.model_validate(response.json())

    def list(
        self,
        *,
        direction: str | None = None,
        status: Sequence[str] | None = None,
        error_code: Sequence[str] | None = None,
        category: str | None = None,
        to: str | None = None,
        from_: str | None = None,
        tag: Sequence[str] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[SMSMessage]:
        """List SMS messages, newest first; iterate the page to auto-paginate.

        ```python
        for message in client.sms.list(direction="outbound"):
            print(message.id, message.status)
        ```
        """
        query = _list_query({
            "direction": direction, "status": status, "error_code": error_code,
            "category": category, "to": to, "from": from_, "tag": tag,
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            "created_after": created_after, "created_before": created_before,
        })
        return SyncPage(self._client, _PATH, query, SMSMessage, options)


class AsyncSms:
    """Async mirror of `Sms`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def send(
        self,
        *,
        to: str,
        from_: str | None = None,
        text: str | None = None,
        category: str | None = None,
        template: str | None = None,
        language: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> SMSMessage:
        """Send one SMS to a single recipient (free text or by template)."""
        body = _send_body(
            to=to, from_=from_, text=text, category=category, template=template,
            language=language, parameters=parameters, tags=tags, metadata=metadata,
        )
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return SMSMessage.model_validate(response.json())

    async def send_batch(
        self, *, messages: Sequence[Mapping[str, Any]], options: RequestOptions | None = None
    ) -> SMSMessageBatchResponse:
        """Send up to 100 independent SMS messages in one call."""
        body = [_message_body(m) for m in messages]
        response = await self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return SMSMessageBatchResponse.model_validate(response.json())

    async def get(self, message_id: str, *, options: RequestOptions | None = None) -> SMSMessage:
        """Fetch a single SMS message with its current status, segments, and cost."""
        response = await self._client.request("GET", f"{_PATH}/{message_id}", **_opts(options))
        return SMSMessage.model_validate(response.json())

    def list(
        self,
        *,
        direction: str | None = None,
        status: Sequence[str] | None = None,
        error_code: Sequence[str] | None = None,
        category: str | None = None,
        to: str | None = None,
        from_: str | None = None,
        tag: Sequence[str] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[SMSMessage]:
        """List SMS messages, newest first; ``async for`` over the page to auto-paginate."""
        query = _list_query({
            "direction": direction, "status": status, "error_code": error_code,
            "category": category, "to": to, "from": from_, "tag": tag,
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            "created_after": created_after, "created_before": created_before,
        })
        return AsyncPage(self._client, _PATH, query, SMSMessage, options)
