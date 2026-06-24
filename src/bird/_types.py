"""Shared SDK-internal types."""

from __future__ import annotations

from typing import Any, Mapping, Sequence, TypedDict, Union

import httpx


# An address accepted by send() — a plain email string, an RFC 5322 mailbox string
# ("Jane Doe <jane@x.com>"), or a dict/EmailAddress object with "email" and optional "name".
EmailAddressInput = Union[str, Mapping[str, str]]


class RequestOptions(TypedDict, total=False):
    """Per-call overrides, passed as the trailing ``options`` argument of any
    resource method (the cross-SDK options object, ADR-0042 §10). Every key is
    optional.
    """

    extra_headers: Mapping[str, str]
    extra_query: Mapping[str, Any]
    extra_body: Mapping[str, Any]
    timeout: float | httpx.Timeout | None
    max_retries: int
    idempotency_key: str


class EmailDefaults(TypedDict, total=False):
    """Workspace-wide defaults for ``client.email.send``, set on the client. A
    per-send value always wins; an unset send field falls back to its default
    (the cross-SDK channel-defaults merge, ADR-0045). Every key is optional.
    """

    from_: EmailAddressInput
    reply_to: Sequence[EmailAddressInput]
    category: str
    track_opens: bool
    track_clicks: bool
    headers: Mapping[str, str]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]


class _AttachmentRequired(TypedDict):
    filename: str
    content: str  # base64-encoded bytes


class Attachment(_AttachmentRequired, total=False):
    """A file attachment for ``client.email.send``. ``filename`` and ``content`` are
    required; ``content`` is the base64-encoded attachment bytes (the SDK does not
    encode for you) and counts against the 20 MB per-send cap. ``content_type`` is
    inferred from the filename when omitted; setting ``content_id`` renders the
    attachment inline (referenceable from the HTML body as ``cid:{content_id}``).
    """

    content_type: str
    content_id: str


# Per-method params types — the dict form of each method's keyword arguments, for
# callers who build the payload as a dict and splat it (``client.email.send(**params)``).
# Parity with Go's request struct / TS's params type (ADR-0045). Keys mirror the
# keyword argument names (``from_``, not the wire ``from``).


class _EmailSendRequired(TypedDict):
    to: Sequence[EmailAddressInput]
    subject: str


class EmailSendParams(_EmailSendRequired, total=False):
    """Params for ``client.email.send``. ``to`` and ``subject`` are required;
    ``from_`` is required unless an ``email_defaults`` from-address is set."""

    from_: EmailAddressInput
    html: str
    text: str
    cc: Sequence[EmailAddressInput]
    bcc: Sequence[EmailAddressInput]
    reply_to: Sequence[EmailAddressInput]
    headers: Mapping[str, str]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]
    track_opens: bool
    track_clicks: bool
    ip_pool_id: str
    category: str
    attachments: Sequence[Attachment]


class _EmailSendBatchRequired(TypedDict):
    messages: Sequence[EmailSendParams]


class EmailSendBatchParams(_EmailSendBatchRequired, total=False):
    """Params for ``client.email.send_batch``. ``messages`` is required — a sequence
    of per-message params (each shaped like ``EmailSendParams``); 1–100 messages,
    all validated before any are queued. An ``email_defaults`` from-address fills an
    unset ``from_`` on each message, exactly as it does for ``send``."""


class EmailListParams(TypedDict, total=False):
    """Filters for ``client.email.list``. Every key is optional."""

    limit: int
    starting_after: str
    ending_before: str
    status: str
    tag: str
    category: str
    to: str
    from_: str


class NotGiven:
    """Sentinel for an argument the caller left unset, distinct from an explicit
    ``None``. ``timeout=None`` means "no timeout"; ``timeout=NOT_GIVEN`` means
    "use the client default". Falsy so ``if not timeout`` reads naturally.
    """

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = NotGiven()

Headers = Mapping[str, str]
Query = Mapping[str, Any]
Body = Any
