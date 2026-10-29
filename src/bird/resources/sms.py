"""Use the ``client.sms`` channel to send an SMS (free text or by stored
template), read a message, and list the message log.

A send carries one of ``text`` (with ``category`` and ``from_``), a ``template``
(by id or slug, with its ``parameters``), or ``binary`` (with ``category``
``transactional``). A workspace template requires an owned ``from_``; a built-in
template selects its sender and rejects ``from_``. The content forms are mutually
exclusive.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import SMSMessage, SMSMessageBatchResponse
from bird._types import Omit, RequestOptions, omit
from bird.resources.sms_gen import AsyncSmsBase, SmsBase
from bird.resources.sms_stats import AsyncSmsStats, SmsStats

_PATH = "/v1/sms/messages"
_BATCH_PATH = "/v1/sms/batches"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})



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
    smart_encoding: bool | None = None,
    ignore_suppression: bool | None = None,
    callback_url: str | None | Omit = omit,
    messaging_profile_id: str | None = None,
    reference: str | None = None,
    to_country_code: str | None = None,
    validity_period: int | None = None,
    cost_center: str | None = None,
    binary: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    # The generated send request is an anyOf(text | template) with no single
    # wrappable model, so the body is assembled as a plain dict here; unset fields
    # are dropped. ``from_`` maps to the wire field "from" (a Python keyword).
    #
    # The wire nests smart_encoding, ignore_suppression and callback_url under
    # "options", but they are flat keywords here: ``options`` on every method in this
    # SDK is the transport RequestOptions, so a second meaning would be a trap. A
    # future send option joins them as its own keyword.
    body: dict[str, Any] = {
        "to": to,
        "from": from_,
        "text": text,
        "category": category,
        "tags": tags,
        "metadata": metadata,
        "messaging_profile_id": messaging_profile_id,
        "reference": reference,
        "to_country_code": to_country_code,
        "validity_period": validity_period,
        "cost_center": cost_center,
        "binary": binary,
    }
    send_options: dict[str, Any] = {
        "smart_encoding": smart_encoding,
        "ignore_suppression": ignore_suppression,
    }
    send_options = {key: value for key, value in send_options.items() if value is not None}
    # None is a value here: a null callback_url sends the message's events to the
    # webhook subscriptions, where omitting it applies the messaging profile's URL.
    if not isinstance(callback_url, Omit):
        send_options["callback_url"] = callback_url
    if send_options:
        body["options"] = send_options
    if template is not None:
        # An smt_-prefixed value is the id; anything else is the slug handle.
        tmpl: dict[str, Any] = {"id" if template.startswith("smt_") else "slug": template}
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
        smart_encoding=m.get("smart_encoding"),
        ignore_suppression=m.get("ignore_suppression"),
        callback_url=m.get("callback_url", omit),
        messaging_profile_id=m.get("messaging_profile_id"),
        reference=m.get("reference"),
        to_country_code=m.get("to_country_code"),
        validity_period=m.get("validity_period"),
        cost_center=m.get("cost_center"),
        binary=m.get("binary"),
    )


class Sms(SmsBase):
    """Send and read SMS messages. Reach it via ``client.sms``."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.stats = SmsStats(client)

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
        smart_encoding: bool | None = None,
        ignore_suppression: bool | None = None,
        callback_url: str | None | Omit = omit,
        messaging_profile_id: str | None = None,
        reference: str | None = None,
        to_country_code: str | None = None,
        validity_period: int | None = None,
        cost_center: str | None = None,
        binary: Mapping[str, str] | None = None,
        options: RequestOptions | None = None,
    ) -> SMSMessage:
        """Send one SMS to a single recipient. Supply one of ``text`` (with a
        ``category`` and ``from_``), a stored ``template`` (by id or slug, with
        ``parameters``), or ``binary`` (with ``category`` ``transactional``). A workspace template requires an owned
        ``from_``; a built-in template selects its sender and rejects ``from_``.
        The API accepts the message for delivery. Read it back with ``get`` for the latest status.

        ``callback_url`` takes three states: leave it out to use the messaging
        profile's URL, pass a URL to receive this message's events there, or pass
        ``None`` to send them to your webhook subscriptions.

        ```python
        msg = client.sms.send(
            from_="+15557654321",
            to="+15551234567",
            text="Your verification code is 123456.",
            category="authentication",
        )
        print(msg.id, msg.status)
        ```

        ```python
        client.sms.send(
            to="+14155550100",
            template="bird_otp_verification",
            parameters={"code": "123456"},
        )
        ```
        """
        body = _send_body(
            to=to, from_=from_, text=text, category=category, template=template,
            language=language, parameters=parameters, tags=tags, metadata=metadata,
            smart_encoding=smart_encoding, ignore_suppression=ignore_suppression,
            callback_url=callback_url, messaging_profile_id=messaging_profile_id,
            reference=reference, to_country_code=to_country_code,
            validity_period=validity_period, cost_center=cost_center, binary=binary,
        )
        return self._write("POST", _PATH, body, SMSMessage, options)

    def send_batch(
        self, *, messages: Sequence[Mapping[str, Any]], options: RequestOptions | None = None
    ) -> SMSMessageBatchResponse:
        """Send up to 100 independent SMS messages in one call. Each item is shaped
        like the keyword arguments of ``send``; all are validated before any queue.

        ```python
        batch = client.sms.send_batch(
            messages=[
                {
                    "from_": "+15557654321",
                    "to": "+15551111111",
                    "text": "Hi Alice!",
                    "category": "marketing",
                },
                {
                    "from_": "+15557654321",
                    "to": "+15552222222",
                    "text": "Hi Bob!",
                    "category": "marketing",
                },
            ]
        )
        for msg in batch.data:
            print(msg.id, msg.status)
        ```
        """
        body = {"messages": [_message_body(m) for m in messages]}
        response = self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return SMSMessageBatchResponse.model_validate(response.json())




class AsyncSms(AsyncSmsBase):
    """Async mirror of `Sms`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.stats = AsyncSmsStats(client)

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
        smart_encoding: bool | None = None,
        ignore_suppression: bool | None = None,
        callback_url: str | None | Omit = omit,
        messaging_profile_id: str | None = None,
        reference: str | None = None,
        to_country_code: str | None = None,
        validity_period: int | None = None,
        cost_center: str | None = None,
        binary: Mapping[str, str] | None = None,
        options: RequestOptions | None = None,
    ) -> SMSMessage:
        """Send one SMS to a single recipient (free text, by template, or binary).

        A workspace template requires an owned ``from_``; a built-in template
        selects its sender and rejects ``from_``.
        """
        body = _send_body(
            to=to, from_=from_, text=text, category=category, template=template,
            language=language, parameters=parameters, tags=tags, metadata=metadata,
            smart_encoding=smart_encoding, ignore_suppression=ignore_suppression,
            callback_url=callback_url, messaging_profile_id=messaging_profile_id,
            reference=reference, to_country_code=to_country_code,
            validity_period=validity_period, cost_center=cost_center, binary=binary,
        )
        return await self._write("POST", _PATH, body, SMSMessage, options)

    async def send_batch(
        self, *, messages: Sequence[Mapping[str, Any]], options: RequestOptions | None = None
    ) -> SMSMessageBatchResponse:
        """Send up to 100 independent SMS messages in one call."""
        body = {"messages": [_message_body(m) for m in messages]}
        response = await self._client.request("POST", _BATCH_PATH, body=body, **_opts(options))
        return SMSMessageBatchResponse.model_validate(response.json())
