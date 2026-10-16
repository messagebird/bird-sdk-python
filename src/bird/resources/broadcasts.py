"""client.broadcasts — one piece of template content sent to a stored audience.

The reads plus ``cancel`` and ``delete`` are generated; ``create``, ``update``
and ``send`` are hand-written because each carries a ``scheduled_at`` the
generator has no wire conversion for, and ``create``/``update`` also carry a
``from`` address union.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence
from urllib.parse import quote

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._exceptions import BirdError
from bird._generated import (
    EmailBroadcast,
    EmailMessage,
    EmailBroadcastValidationResult,
    EmailBroadcastValidationRequest,
    EmailBroadcastPreviewRequest,
    EmailBroadcastTestRequest,
    EmailBroadcastPreviewResult,
    EmailBroadcastCreateRequest,
    EmailBroadcastSendNowRequest,
    EmailBroadcastUpdateRequest,
)
from bird._models import to_wire, to_wire_exclude_unset
from bird._types import EmailAddressInput, EmailDefaults, Omit, RequestOptions, omit
from bird.resources.broadcasts_gen import AsyncBroadcastsBase, BroadcastsBase

_NAIVE_SCHEDULED_AT = (
    "scheduled_at requires a timezone-aware datetime (e.g. tzinfo=timezone.utc): "
    "the API measures the delay from now in absolute time, so an offset-less "
    "value has no defined meaning on the wire"
)


def _scheduled_at_wire(value: str | datetime | None) -> str | None:
    """RFC 3339 with an explicit offset. A string is already wire-shaped and
    passes through verbatim; a naive ``datetime`` (no ``tzinfo``) is rejected
    rather than silently assumed to be UTC. A zero offset is written ``Z``,
    which is what the conformance vectors and the other three SDKs emit --
    ``isoformat()`` alone gives ``+00:00``."""
    if not isinstance(value, datetime):
        return value
    if value.utcoffset() is None:
        raise BirdError(_NAIVE_SCHEDULED_AT)
    return value.isoformat().replace("+00:00", "Z")


# The email defaults a broadcast create accepts, derived rather than listed so a
# field added to EmailDefaults reaches it for free. Only ``from_`` is spelled
# differently on the wire, which the merge below maps.
_BROADCAST_DEFAULT_KEYS = tuple(
    k for k in EmailDefaults.__annotations__ if k in EmailBroadcastCreateRequest.model_fields
)


def _given(value: Any) -> bool:
    return value is not None and not isinstance(value, Omit)


def _overrides_wire(overrides: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    # A complete replacement map: a null language here would otherwise become a destructive
    # {} clear, so both levels must already be mappings. Scalar None inside one stays null.
    if not isinstance(overrides, Mapping) or not all(isinstance(values, Mapping) for values in overrides.values()):
        raise BirdError("template.parameter_overrides must map each language to a JSON object")
    return {language: dict(values) for language, values in overrides.items()}


def _create_template(
    template: str | None, language: str | None, parameters: Mapping[str, Any] | None | Omit,
    parameter_overrides: Mapping[str, Mapping[str, Any]] | None | Omit = omit,
) -> dict[str, Any] | None:
    # The language is one of the template's own languages, so it travels inside
    # the template reference rather than beside it.
    if template is None:
        if _given(parameters) or _given(parameter_overrides):
            raise ValueError("parameters needs a template")
        if language is not None:
            raise ValueError("language needs a template: the language is chosen from the template it belongs to")
        return None
    nested: dict[str, Any] = {"id": template}
    if language is not None:
        nested["language"] = language
    return nested


def _create_body(
    from_: EmailAddressInput | None,
    audience_id: str | None,
    template: str | None,
    reply_to: Sequence[EmailAddressInput] | None,
    headers: Mapping[str, str] | None,
    tags: Sequence[Mapping[str, str]] | None,
    metadata: Mapping[str, Any] | None,
    track_opens: bool | None,
    track_clicks: bool | None,
    ip_pool_id: str | None,
    category: str | None,
    send: bool | None,
    scheduled_at: str | datetime | None,
    defaults: EmailDefaults | None = None,
    language: str | None = None,
    parameters: Mapping[str, Any] | None | Omit = omit,
    parameter_overrides: Mapping[str, Mapping[str, Any]] | None | Omit = omit,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "from": from_,
        "audience_id": audience_id,
        "template": _create_template(template, language, parameters, parameter_overrides),
        "reply_to": reply_to,
        "headers": headers,
        "tags": tags,
        "metadata": metadata,
        "track_opens": track_opens,
        "track_clicks": track_clicks,
        "ip_pool_id": ip_pool_id,
        "category": category,
        "send": send,
        "scheduled_at": _scheduled_at_wire(scheduled_at),
    }
    # A per-call value always wins; an unset field falls back to the client
    # default. Create only -- an update leaves an unset field at whatever the
    # draft holds, so a default filled there would overwrite a stored value the
    # caller never named.
    if defaults:
        for key in _BROADCAST_DEFAULT_KEYS:
            wire = "from" if key == "from_" else key
            if fields.get(wire) is None and (value := defaults.get(key)) is not None:
                fields[wire] = value
    body = to_wire(EmailBroadcastCreateRequest, fields)
    if parameters is not None and not isinstance(parameters, Omit):
        body["template"]["parameters"] = dict(parameters)
    if parameter_overrides is not None and not isinstance(parameter_overrides, Omit):
        body["template"]["parameter_overrides"] = _overrides_wire(parameter_overrides)
    return body


def _update_body(
    from_: EmailAddressInput | None,
    audience_id: str | None,
    template: str | None | Omit,
    reply_to: Sequence[EmailAddressInput] | None | Omit,
    headers: Mapping[str, str] | None,
    tags: Sequence[Mapping[str, str]] | None,
    metadata: Mapping[str, Any] | None,
    track_opens: bool | None,
    track_clicks: bool | None,
    ip_pool_id: str | None | Omit,
    category: str | None,
    language: str | None | Omit = omit,
    parameters: Mapping[str, Any] | None | Omit = omit,
    parameter_overrides: Mapping[str, Mapping[str, Any]] | None | Omit = omit,
) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if from_ is not None:
        body["from"] = from_
    if audience_id is not None:
        body["audience_id"] = audience_id
    # None clears (JSON null); omit leaves the stored value unchanged. The two
    # are distinct on the wire, so the sentinel is what separates them. Naming a
    # template releases the version the broadcast is fixed to, so a language on
    # its own is sent without an id and keeps it.
    # Clearing the template clears its language too, so ``language=None``
    # beside ``template=None`` asks for the same clear twice and goes through.
    if not isinstance(template, Omit) and template is None:
        if _given(parameters) or _given(parameter_overrides):
            raise ValueError("parameters cannot accompany a cleared template")
        if not isinstance(language, Omit) and language is not None:
            raise ValueError("language needs a template: the language is chosen from the template it belongs to")
        body["template"] = None
    elif (
        not isinstance(template, Omit) or not isinstance(language, Omit)
        or _given(parameters) or _given(parameter_overrides)
    ):
        nested: dict[str, Any] = {}
        if not isinstance(template, Omit):
            nested["id"] = template
        if not isinstance(language, Omit):
            nested["language"] = language
        body["template"] = nested
    if not isinstance(reply_to, Omit):
        body["reply_to"] = reply_to
    if headers is not None:
        body["headers"] = headers
    if tags is not None:
        body["tags"] = tags
    if metadata is not None:
        body["metadata"] = metadata
    if track_opens is not None:
        body["track_opens"] = track_opens
    if track_clicks is not None:
        body["track_clicks"] = track_clicks
    if not isinstance(ip_pool_id, Omit):
        body["ip_pool_id"] = ip_pool_id
    if category is not None:
        body["category"] = category
    wire = to_wire_exclude_unset(EmailBroadcastUpdateRequest, body)
    if parameters is not None and not isinstance(parameters, Omit):
        wire["template"]["parameters"] = dict(parameters)
    if parameter_overrides is not None and not isinstance(parameter_overrides, Omit):
        wire["template"]["parameter_overrides"] = _overrides_wire(parameter_overrides)
    return wire


def _send_body(scheduled_at: str | datetime | None) -> dict[str, Any]:
    return to_wire(
        EmailBroadcastSendNowRequest, {"scheduled_at": _scheduled_at_wire(scheduled_at)}
    )



def _parameter_operation_body(
    template: Mapping[str, Any] | None | Omit,
    from_: EmailAddressInput | Omit,
    reply_to: Sequence[EmailAddressInput] | None | Omit,
    headers: Mapping[str, str] | Omit,
    contact_id: str | Omit = omit,
) -> dict[str, Any]:
    if isinstance(template, Mapping) and "parameters" in template:
        if not isinstance(template["parameters"], Mapping):
            raise BirdError("template.parameters must be a non-null JSON object")
    if isinstance(template, Mapping) and "parameter_overrides" in template:
        overrides = template["parameter_overrides"]
        if not isinstance(overrides, Mapping) or not all(isinstance(v, Mapping) for v in overrides.values()):
            raise BirdError("template.parameter_overrides must map each language to a JSON object")
    body: dict[str, Any] = {}
    for key, value in (("template", template), ("from", from_), ("reply_to", reply_to), ("headers", headers), ("contact_id", contact_id)):
        if not isinstance(value, Omit):
            body[key] = value
    return body

class Broadcasts(BroadcastsBase):
    """Broadcasts: draft, update, send, cancel, and read how one landed. Reach
    it via ``client.broadcasts``."""

    def __init__(self, client: SyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self._defaults = defaults

    def create(
        self,
        *,
        from_: EmailAddressInput | None = None,
        audience_id: str | None = None,
        template: str | None = None,
        reply_to: Sequence[EmailAddressInput] | None = None,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None = None,
        category: str | None = None,
        language: str | None = None,
        parameters: Mapping[str, Any] | None | Omit = omit,
        parameter_overrides: Mapping[str, Mapping[str, Any]] | None | Omit = omit,
        send: bool | None = None,
        scheduled_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Create a broadcast. It is a draft unless ``send`` is set, in which
        case it goes out immediately, or at ``scheduled_at`` when one is given.
        A send needs a ``from_`` on a verified domain, an ``audience_id``, and a
        ``template`` with a published version; without them the call is refused
        with a ``422`` rather than saved as a draft. ``language`` selects one of
        the template's languages for the whole audience and needs ``template``;
        it has to be an exact match for a language on the published version, so
        ``fr-CA`` does not select ``fr``.

        ```python
        broadcast = client.broadcasts.create(
            from_="newsletter@example.com",
            audience_id="adn_01krdgeqcxet5s7t44vh8rt9mg",
            template="emt_01krdgeqcxet5s7t44vh8rt9mg",
        )
        print(broadcast.id, broadcast.status)
        ```
        """
        body = _create_body(
            from_, audience_id, template, reply_to, headers, tags, metadata,
            track_opens, track_clicks, ip_pool_id, category, send, scheduled_at,
            self._defaults, language, parameters, parameter_overrides,
        )
        return self._write("POST", "/v1/email/broadcasts", body, EmailBroadcast, options)

    def update(
        self,
        broadcast_id: str,
        *,
        from_: EmailAddressInput | None = None,
        audience_id: str | None = None,
        template: str | None | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None | Omit = omit,
        category: str | None = None,
        language: str | None | Omit = omit,
        parameters: Mapping[str, Any] | None | Omit = omit,
        parameter_overrides: Mapping[str, Mapping[str, Any]] | None | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Change a broadcast that is still a draft or is scheduled, and return
        it as it now stands. Omitted arguments keep their current value;
        ``template``, ``language``, ``reply_to`` and ``ip_pool_id`` take
        ``None`` to clear. A broadcast that has started sending can no longer be edited
        and raises a ``409``.

        ```python
        broadcast = client.broadcasts.update(
            "eb_01krdgeqcxet5s7t44vh8rt9mg",
            template="emt_01krdgeqcxet5s7t44vh8rt9mg",
        )
        print(broadcast.status)
        ```
        """
        body = _update_body(
            from_, audience_id, template, reply_to, headers, tags, metadata,
            track_opens, track_clicks, ip_pool_id, category, language, parameters,
            parameter_overrides,
        )
        return self._write(
            "PATCH",
            f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}",
            body,
            EmailBroadcast,
            options,
        )

    def send(
        self,
        broadcast_id: str,
        *,
        scheduled_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Send a draft broadcast, immediately or at ``scheduled_at``. The
        broadcast needs a ``from_`` on a verified domain, an ``audience_id``,
        and a ``template`` with a published version. One that has already
        started sending or has reached a final state raises a ``409``.

        ```python
        broadcast = client.broadcasts.send("eb_01krdgeqcxet5s7t44vh8rt9mg")
        print(broadcast.status)
        ```
        """
        return self._write(
            "POST",
            f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/send",
            _send_body(scheduled_at),
            EmailBroadcast,
            options,
        )

    def validate(
        self,
        broadcast_id: str,
        *,
        template: Mapping[str, Any] | None | Omit = omit,
        from_: EmailAddressInput | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailBroadcastValidationResult:
        """Check the broadcast's saved inputs, or the ones given here, against
        the template's current published version without saving anything or
        evaluating recipients. ``template`` takes the same ``language``,
        ``parameters`` and ``parameter_overrides`` an update would; omitted
        arguments use what the broadcast already has.

        ```python
        result = client.broadcasts.validate(
            "eb_01krdgeqcxet5s7t44vh8rt9mg",
            template={"parameters": {"title": "Welcome", "discount": 20}},
        )
        print(result.ready_for_admission, result.problems)
        ```
        """
        body = _parameter_operation_body(template, from_, reply_to, headers)
        body = to_wire_exclude_unset(EmailBroadcastValidationRequest, body)
        return self._write("POST", f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/validate", body, EmailBroadcastValidationResult, options)

    def preview(
        self,
        broadcast_id: str,
        *,
        contact_id: str | Omit = omit,
        template: Mapping[str, Any] | None | Omit = omit,
        from_: EmailAddressInput | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailBroadcastPreviewResult:
        """Render the broadcast's current published content for one contact,
        using its actual values and the inputs given here, without sending
        mail. Pass ``contact_id`` when the template reads contact data; the
        returned ``preview_fingerprint`` is what ``test`` repeats.

        ```python
        preview = client.broadcasts.preview(
            "eb_01krdgeqcxet5s7t44vh8rt9mg",
            template={"parameters": {"title": "Welcome", "discount": 20}},
            contact_id="con_01krdgeqcxet5s7t44vh8rt9mg",
        )
        print(preview.subject, preview.preview_fingerprint)
        ```
        """
        body = _parameter_operation_body(template, from_, reply_to, headers, contact_id)
        body = to_wire_exclude_unset(EmailBroadcastPreviewRequest, body)
        return self._write("POST", f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/preview", body, EmailBroadcastPreviewResult, options)

    def test(
        self,
        broadcast_id: str,
        *,
        contact_id: str | Omit = omit,
        to: str,
        preview_fingerprint: str,
        template: Mapping[str, Any] | None | Omit = omit,
        from_: EmailAddressInput | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailMessage:
        """Send the exact content a fresh preview rendered to one authorized
        member of your organization, never to the broadcast's audience. Repeat
        the preview's inputs and its ``preview_fingerprint``; if the
        publication, inputs or contact changed since, it raises a ``409``.
        Reuse one ``idempotency_key`` per intent so a retry sends once.

        ```python
        template = {"parameters": {"title": "Welcome", "discount": 20}}
        contact_id = "con_01krdgeqcxet5s7t44vh8rt9mg"
        preview = client.broadcasts.preview(
            "eb_01krdgeqcxet5s7t44vh8rt9mg", template=template, contact_id=contact_id
        )
        accepted = client.broadcasts.test(
            "eb_01krdgeqcxet5s7t44vh8rt9mg",
            template=template,
            contact_id=contact_id,
            to="member@example.com",
            preview_fingerprint=preview.preview_fingerprint,
            options={"idempotency_key": "broadcast-preview-intent-1"},
        )
        print(accepted.id, accepted.status)
        ```
        """
        body = _parameter_operation_body(template, from_, reply_to, headers, contact_id)
        body["to"] = to
        body["preview_fingerprint"] = preview_fingerprint
        body = to_wire_exclude_unset(EmailBroadcastTestRequest, body)
        if not options or not options.get("idempotency_key"):
            raise BirdError("broadcasts.test requires a nonempty caller idempotency_key")
        return self._write("POST", f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/test", body, EmailMessage, options)


class AsyncBroadcasts(AsyncBroadcastsBase):
    """Async mirror of `Broadcasts`."""

    def __init__(self, client: AsyncAPIClient, defaults: EmailDefaults | None = None) -> None:
        super().__init__(client)
        self._defaults = defaults

    async def create(
        self,
        *,
        from_: EmailAddressInput | None = None,
        audience_id: str | None = None,
        template: str | None = None,
        reply_to: Sequence[EmailAddressInput] | None = None,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None = None,
        category: str | None = None,
        language: str | None = None,
        parameters: Mapping[str, Any] | None | Omit = omit,
        parameter_overrides: Mapping[str, Mapping[str, Any]] | None | Omit = omit,
        send: bool | None = None,
        scheduled_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Create a broadcast. See `Broadcasts.create`."""
        body = _create_body(
            from_, audience_id, template, reply_to, headers, tags, metadata,
            track_opens, track_clicks, ip_pool_id, category, send, scheduled_at,
            self._defaults, language, parameters, parameter_overrides,
        )
        return await self._write("POST", "/v1/email/broadcasts", body, EmailBroadcast, options)

    async def update(
        self,
        broadcast_id: str,
        *,
        from_: EmailAddressInput | None = None,
        audience_id: str | None = None,
        template: str | None | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
        track_opens: bool | None = None,
        track_clicks: bool | None = None,
        ip_pool_id: str | None | Omit = omit,
        category: str | None = None,
        language: str | None | Omit = omit,
        parameters: Mapping[str, Any] | None | Omit = omit,
        parameter_overrides: Mapping[str, Mapping[str, Any]] | None | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Change a draft or scheduled broadcast. See `Broadcasts.update`."""
        body = _update_body(
            from_, audience_id, template, reply_to, headers, tags, metadata,
            track_opens, track_clicks, ip_pool_id, category, language, parameters,
            parameter_overrides,
        )
        return await self._write(
            "PATCH",
            f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}",
            body,
            EmailBroadcast,
            options,
        )

    async def send(
        self,
        broadcast_id: str,
        *,
        scheduled_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> EmailBroadcast:
        """Send a draft broadcast. See `Broadcasts.send`."""
        return await self._write(
            "POST",
            f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/send",
            _send_body(scheduled_at),
            EmailBroadcast,
            options,
        )

    async def validate(
        self,
        broadcast_id: str,
        *,
        template: Mapping[str, Any] | None | Omit = omit,
        from_: EmailAddressInput | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailBroadcastValidationResult:
        """Check a broadcast's inputs without saving. See `Broadcasts.validate`."""
        body = _parameter_operation_body(template, from_, reply_to, headers)
        body = to_wire_exclude_unset(EmailBroadcastValidationRequest, body)
        return await self._write("POST", f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/validate", body, EmailBroadcastValidationResult, options)

    async def preview(
        self,
        broadcast_id: str,
        *,
        contact_id: str | Omit = omit,
        template: Mapping[str, Any] | None | Omit = omit,
        from_: EmailAddressInput | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailBroadcastPreviewResult:
        """Render a broadcast for one contact. See `Broadcasts.preview`."""
        body = _parameter_operation_body(template, from_, reply_to, headers, contact_id)
        body = to_wire_exclude_unset(EmailBroadcastPreviewRequest, body)
        return await self._write("POST", f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/preview", body, EmailBroadcastPreviewResult, options)

    async def test(
        self,
        broadcast_id: str,
        *,
        contact_id: str | Omit = omit,
        to: str,
        preview_fingerprint: str,
        template: Mapping[str, Any] | None | Omit = omit,
        from_: EmailAddressInput | Omit = omit,
        reply_to: Sequence[EmailAddressInput] | None | Omit = omit,
        headers: Mapping[str, str] | Omit = omit,
        options: RequestOptions | None = None,
    ) -> EmailMessage:
        """Send a rendered test to one member. See `Broadcasts.test`."""
        body = _parameter_operation_body(template, from_, reply_to, headers, contact_id)
        body["to"] = to
        body["preview_fingerprint"] = preview_fingerprint
        body = to_wire_exclude_unset(EmailBroadcastTestRequest, body)
        if not options or not options.get("idempotency_key"):
            raise BirdError("broadcasts.test requires a nonempty caller idempotency_key")
        return await self._write("POST", f"/v1/email/broadcasts/{quote(broadcast_id, safe='')}/test", body, EmailMessage, options)
