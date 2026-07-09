"""The email channel: ``client.email.send`` / ``get`` / ``list``."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._exceptions import BirdError
from bird._generated import (
    EmailMessage,
    EmailMessageBatchRequest,
    EmailMessageBatchResponse,
    EmailMessageSendRequest,
)
from bird._models import to_wire
from bird._response import APIResponse
from bird._types import (
    Attachment,
    EmailAddressInput,
    EmailDefaults,
    EmailSendParams,
    RequestOptions,
)
from bird.pagination import AsyncPage, SyncPage

_BATCH_PATH = "/v1/email/batches"

_PATH = "/v1/email/messages"


def _parse_address(addr: EmailAddressInput) -> str | dict[str, str]:
    """Pass an address through to the wire verbatim — no client-side parsing.

    The wire's string form accepts both a plain address and an RFC 5322 mailbox
    with a display name ("Jane <jane@x.com>"), so the server parses; a dict /
    EmailAddress is passed through as the object form.
    """
    if isinstance(addr, str):
        return addr
    return dict(addr)  # type: ignore[arg-type]


def _parse_address_list(
    addrs: Sequence[EmailAddressInput] | None,
) -> list[str | dict[str, str]] | None:
    if addrs is None:
        return None
    return [_parse_address(a) for a in addrs]


def _send_body(
    *,
    from_: EmailAddressInput | None,
    to: Sequence[EmailAddressInput],
    subject: str | None,
    html: str | None,
    text: str | None,
    template: str | None,
    parameters: Mapping[str, Any] | None,
    cc: Sequence[EmailAddressInput] | None,
    bcc: Sequence[EmailAddressInput] | None,
    reply_to: Sequence[EmailAddressInput] | None,
    headers: Mapping[str, str] | None,
    tags: Sequence[Mapping[str, str]] | None,
    metadata: Mapping[str, Any] | None,
    track_opens: bool | None,
    track_clicks: bool | None,
    ip_pool_id: str | None,
    category: str | None,
    attachments: Sequence[Attachment] | None,
    defaults: EmailDefaults | None,
) -> dict[str, Any]:
    # A per-send value wins; an unset field falls back to the client's EmailDefaults
    # (ADR-0045). `from_` maps to the wire field "from" (a Python keyword). `template`
    # and `parameters` are per-send only (not defaultable).
    d = defaults or {}
    raw_from = from_ if from_ is not None else d.get("from_")
    raw_reply_to = reply_to if reply_to is not None else d.get("reply_to")
    return to_wire(EmailMessageSendRequest, {
        "from":         _parse_address(raw_from) if raw_from is not None else None,
        "to":           _parse_address_list(to),
        "subject":      subject,
        "html":         html,
        "text":         text,
        # A template send nests its reference (id or name) and variables under the
        # template object; an inline send uses the top-level parameters (the two
        # content modes are exclusive). The `emt_` prefix marks an id, else a name.
        "template": (
            {("id" if template.startswith("emt_") else "name"): template, "parameters": parameters}
            if template is not None else None
        ),
        "parameters":   parameters if template is None else None,
        "cc":           _parse_address_list(cc),
        "bcc":          _parse_address_list(bcc),
        "reply_to":     _parse_address_list(raw_reply_to),  # type: ignore[arg-type]
        "headers":      headers      if headers      is not None else d.get("headers"),
        "tags":         tags         if tags         is not None else d.get("tags"),
        "metadata":     metadata     if metadata     is not None else d.get("metadata"),
        "track_opens":  track_opens  if track_opens  is not None else d.get("track_opens"),
        "track_clicks": track_clicks if track_clicks is not None else d.get("track_clicks"),
        "ip_pool_id":      ip_pool_id,
        "category":     category     if category     is not None else d.get("category"),
        "attachments":  attachments,
    })


def _batch_body(
    messages: Sequence[EmailSendParams],
    defaults: EmailDefaults | None,
) -> list[dict[str, Any]]:
    # Each item is built exactly like a single send (address parsing, the from_->"from"
    # alias, the EmailDefaults merge, exclude_none) via _send_body, which validates the
    # item through EmailMessageSendRequest. The list's own 1..100 length bound is checked
    # against the generated RootModel's field constraints so a too-short/long batch fails
    # client-side as a BirdError, mirroring to_wire — without re-dumping the items (that
    # would re-apply model defaults and undo exclude_none).
    items = [
        _send_body(
            from_=m.get("from_"),
            to=m["to"],
            subject=m.get("subject"),
            html=m.get("html"),
            text=m.get("text"),
            template=m.get("template"),
            parameters=m.get("parameters"),
            cc=m.get("cc"),
            bcc=m.get("bcc"),
            reply_to=m.get("reply_to"),
            headers=m.get("headers"),
            tags=m.get("tags"),
            metadata=m.get("metadata"),
            track_opens=m.get("track_opens"),
            track_clicks=m.get("track_clicks"),
            ip_pool_id=m.get("ip_pool_id"),
            category=m.get("category"),
            attachments=m.get("attachments"),
            defaults=defaults,
        )
        for m in messages
    ]
    field = EmailMessageBatchRequest.model_fields["root"]
    lo = next((m.min_length for m in field.metadata if hasattr(m, "min_length")), None)
    hi = next((m.max_length for m in field.metadata if hasattr(m, "max_length")), None)
    if (lo is not None and len(items) < lo) or (hi is not None and len(items) > hi):
        raise BirdError(f"invalid request: messages: list must have between {lo} and {hi} items, got {len(items)}")
    return items


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


class Email:
    def __init__(self, client: SyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        self._client = client
        self._defaults = defaults

    @property
    def with_raw_response(self) -> "EmailWithRawResponse":
        """Same methods, but each returns an `APIResponse` exposing status, headers,
        and `request_id` alongside `.parse()`."""
        return EmailWithRawResponse(self._client, self._defaults)

    def send(
        self,
        *,
        from_: EmailAddressInput | None = None,
        to: Sequence[EmailAddressInput],
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        template: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        cc: Sequence[EmailAddressInput] | None = None,
        bcc: Sequence[EmailAddressInput] | None = None,
        reply_to: Sequence[EmailAddressInput] | None = None,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None = None,
        category: str | None = None,
        attachments: Sequence[Attachment] | None = None,
        options: RequestOptions | None = None,
    ) -> EmailMessage:
        """Send an email and return the created message.

        Each address (``from_``, ``to``, ``cc``, ``bcc``, ``reply_to``) accepts a plain
        email string (``"jane@x.com"``), an RFC 5322 mailbox string
        (``"Jane Doe <jane@x.com>"``), or a dict/``EmailAddress`` object
        (``{"email": "jane@x.com", "name": "Jane Doe"}``). Strings are sent verbatim;
        the server accepts both plain addresses and RFC 5322 mailbox form and normalises them.

        ```python
        msg = client.email.send(
            from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
            to=["delivered@messagebird.dev"],
            subject="Hello from Bird",
            html="<p>My first Bird email.</p>",
        )
        print(msg.id, msg.status)
        ```

        Pass ``options`` for per-call overrides (``timeout``, ``idempotency_key``, …):

        ```python
        client.email.send(
            from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
            to=["delivered@messagebird.dev"],
            subject="Hello from Bird",
            text="My first Bird email.",
            options={"timeout": 10, "max_retries": 0},
        )
        ```

        A failure raises a typed ``APIError``; catch the subclasses you act on:

        ```python
        from bird import APIStatusError, RateLimitError, ValidationError

        try:
            client.email.send(
                from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
                to=["delivered@messagebird.dev"],
                subject="Hello from Bird",
                text="My first Bird email.",
            )
        except RateLimitError as err:
            print("rate limited; retry after", err.retry_after)
        except ValidationError as err:
            print(err.status_code, err.details)
        except APIStatusError as err:
            print(err.status_code, err.code, err.request_id)
        ```
        """
        body = _send_body(
            from_=from_, to=to, subject=subject, html=html, text=text,
            template=template, parameters=parameters,
            cc=cc, bcc=bcc, reply_to=reply_to, headers=headers, tags=tags,
            metadata=metadata, track_opens=track_opens, track_clicks=track_clicks,
            ip_pool_id=ip_pool_id, category=category, attachments=attachments,
            defaults=self._defaults,
        )
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return EmailMessage.model_validate(response.json())

    def send_batch(
        self,
        *,
        messages: Sequence[EmailSendParams],
        options: RequestOptions | None = None,
    ) -> EmailMessageBatchResponse:
        """Send a batch of emails in one request and return one result per message.

        ``messages`` is a sequence of per-message params, each shaped exactly like the
        keyword arguments of :meth:`send` (an ``EmailSendParams`` dict). The batch holds
        1–100 messages; the server validates every message before queuing any. The
        client's ``email_defaults`` fill each message's unset fields, and a per-message
        value always wins — the same merge :meth:`send` applies.

        ```python
        batch = client.email.send_batch(
            messages=[
                {
                    "from_": {"email": "onboarding@messagebird.dev", "name": "Bird"},
                    "to": ["delivered@messagebird.dev"],
                    "subject": "Hello from Bird",
                    "html": "<p>My first Bird email.</p>",
                },
                {
                    "from_": {"email": "onboarding@messagebird.dev", "name": "Bird"},
                    "to": ["someone-else@messagebird.dev"],
                    "subject": "Hello again from Bird",
                    "text": "My second Bird email.",
                },
            ],
        )
        for item in batch.data:
            print(item.id, item.status)
        ```
        """
        body = _batch_body(messages, self._defaults)
        response = self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return EmailMessageBatchResponse.model_validate(response.json())

    def get(self, message_id: str, *, options: RequestOptions | None = None) -> EmailMessage:
        """Fetch a previously sent message by id."""
        response = self._client.request("GET", f"{_PATH}/{message_id}", **_opts(options))
        return EmailMessage.model_validate(response.json())

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        category: str | None = None,
        to: str | None = None,
        from_: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[EmailMessage]:
        """List messages, newest first; iterate the page to auto-paginate.

        ```python
        for message in client.email.list(status="delivered"):
            print(message.id)
        page = client.email.list(status="delivered")  # page.data, page.next_cursor
        print(len(page.data), page.next_cursor)
        ```
        """
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            "status": status, "tag": tag, "category": category, "to": to, "from": from_,
            "created_after": created_after, "created_before": created_before,
        })
        return SyncPage(self._client, _PATH, query, EmailMessage, options)


class AsyncEmail:
    """Async mirror of `Email`: ``await`` each call, ``async for`` over a list.

    ```python
    from bird import AsyncBird

    async with AsyncBird() as client:
        async for message in client.email.list(status="delivered"):
            print(message.id)
    ```
    """

    def __init__(self, client: AsyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        self._client = client
        self._defaults = defaults

    @property
    def with_raw_response(self) -> "AsyncEmailWithRawResponse":
        return AsyncEmailWithRawResponse(self._client, self._defaults)

    async def send(
        self,
        *,
        from_: EmailAddressInput | None = None,
        to: Sequence[EmailAddressInput],
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        template: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        cc: Sequence[EmailAddressInput] | None = None,
        bcc: Sequence[EmailAddressInput] | None = None,
        reply_to: Sequence[EmailAddressInput] | None = None,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None = None,
        category: str | None = None,
        attachments: Sequence[Attachment] | None = None,
        options: RequestOptions | None = None,
    ) -> EmailMessage:
        body = _send_body(
            from_=from_, to=to, subject=subject, html=html, text=text,
            template=template, parameters=parameters,
            cc=cc, bcc=bcc, reply_to=reply_to, headers=headers, tags=tags,
            metadata=metadata, track_opens=track_opens, track_clicks=track_clicks,
            ip_pool_id=ip_pool_id, category=category, attachments=attachments,
            defaults=self._defaults,
        )
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return EmailMessage.model_validate(response.json())

    async def send_batch(
        self,
        *,
        messages: Sequence[EmailSendParams],
        options: RequestOptions | None = None,
    ) -> EmailMessageBatchResponse:
        body = _batch_body(messages, self._defaults)
        response = await self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return EmailMessageBatchResponse.model_validate(response.json())

    async def get(self, message_id: str, *, options: RequestOptions | None = None) -> EmailMessage:
        response = await self._client.request("GET", f"{_PATH}/{message_id}", **_opts(options))
        return EmailMessage.model_validate(response.json())

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        category: str | None = None,
        to: str | None = None,
        from_: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[EmailMessage]:
        query = _list_query({
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
            "status": status, "tag": tag, "category": category, "to": to, "from": from_,
            "created_after": created_after, "created_before": created_before,
        })
        return AsyncPage(self._client, _PATH, query, EmailMessage, options)


class EmailWithRawResponse:
    """`Email` methods that return an `APIResponse` (status, headers, request_id, `.parse()`)."""

    def __init__(self, client: SyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        self._client = client
        self._defaults = defaults

    def send(
        self, *, from_: EmailAddressInput | None = None, to: Sequence[EmailAddressInput],
        subject: str | None = None, html: str | None = None, text: str | None = None,
        template: str | None = None, parameters: Mapping[str, Any] | None = None,
        cc: Sequence[EmailAddressInput] | None = None, bcc: Sequence[EmailAddressInput] | None = None,
        reply_to: Sequence[EmailAddressInput] | None = None, headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None, metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None, track_clicks: bool | None = None,
        ip_pool_id: str | None = None, category: str | None = None,
        attachments: Sequence[Attachment] | None = None, options: RequestOptions | None = None,
    ) -> APIResponse[EmailMessage]:
        body = _send_body(
            from_=from_, to=to, subject=subject, html=html, text=text,
            template=template, parameters=parameters,
            cc=cc, bcc=bcc, reply_to=reply_to, headers=headers, tags=tags,
            metadata=metadata, track_opens=track_opens, track_clicks=track_clicks,
            ip_pool_id=ip_pool_id, category=category, attachments=attachments,
            defaults=self._defaults,
        )
        return APIResponse(self._client.request("POST", _PATH, body=body, **_opts(options)), EmailMessage)

    def get(self, message_id: str, *, options: RequestOptions | None = None) -> APIResponse[EmailMessage]:
        return APIResponse(self._client.request("GET", f"{_PATH}/{message_id}", **_opts(options)), EmailMessage)


class AsyncEmailWithRawResponse:
    """Async mirror of `EmailWithRawResponse`."""

    def __init__(self, client: AsyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        self._client = client
        self._defaults = defaults

    async def send(
        self, *, from_: EmailAddressInput | None = None, to: Sequence[EmailAddressInput],
        subject: str | None = None, html: str | None = None, text: str | None = None,
        template: str | None = None, parameters: Mapping[str, Any] | None = None,
        cc: Sequence[EmailAddressInput] | None = None, bcc: Sequence[EmailAddressInput] | None = None,
        reply_to: Sequence[EmailAddressInput] | None = None, headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None, metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None, track_clicks: bool | None = None,
        ip_pool_id: str | None = None, category: str | None = None,
        attachments: Sequence[Attachment] | None = None, options: RequestOptions | None = None,
    ) -> APIResponse[EmailMessage]:
        body = _send_body(
            from_=from_, to=to, subject=subject, html=html, text=text,
            template=template, parameters=parameters,
            cc=cc, bcc=bcc, reply_to=reply_to, headers=headers, tags=tags,
            metadata=metadata, track_opens=track_opens, track_clicks=track_clicks,
            ip_pool_id=ip_pool_id, category=category, attachments=attachments,
            defaults=self._defaults,
        )
        return APIResponse(await self._client.request("POST", _PATH, body=body, **_opts(options)), EmailMessage)

    async def get(self, message_id: str, *, options: RequestOptions | None = None) -> APIResponse[EmailMessage]:
        return APIResponse(await self._client.request("GET", f"{_PATH}/{message_id}", **_opts(options)), EmailMessage)
