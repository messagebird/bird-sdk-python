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


class EmailSendParams(_EmailSendRequired, total=False):
    """Params for ``client.email.send``. ``to`` is required, and ``from_`` is
    required unless an ``email_defaults`` from-address is set. A send is either
    inline (``subject`` plus ``html``/``text``) or by ``template`` — with a
    template, omit ``subject``/``html``/``text`` and personalize with
    ``parameters``."""

    from_: EmailAddressInput
    subject: str
    html: str
    text: str
    template: str
    parameters: Mapping[str, Any]
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


class _SmsSendRequired(TypedDict):
    to: str


class SmsSendParams(_SmsSendRequired, total=False):
    """Params for ``client.sms.send``. ``to`` is required. A send is either
    free-text (``text`` plus ``category``) or by ``template`` — with a template,
    omit ``text``/``category`` and personalize with ``parameters``. ``template``
    is the template's id (``smt_`` prefix) or its name."""

    from_: str
    text: str
    category: str
    template: str
    language: str
    parameters: Mapping[str, Any]
    tags: Sequence[Mapping[str, str]]
    metadata: Mapping[str, Any]


class _WhatsappSendRequired(TypedDict):
    to: str


class WhatsappSendParams(_WhatsappSendRequired, total=False):
    """Params for ``client.whatsapp.send``. ``to`` is required. A send must
    currently include a ``template`` (the only supported content type);
    ``language`` and ``components`` personalize it."""

    template: str
    language: str
    components: Sequence[Mapping[str, Any]]


class VerificationCreateParams(TypedDict, total=False):
    """Params for ``client.verify.verifications.create``. Provide ``email``,
    ``phone``, or both; every key is optional."""

    email: str
    phone: str
    code_length: int
    channels: Sequence[str]
    metadata: Mapping[str, Any]


class _VerificationCheckRequired(TypedDict):
    code: str


class VerificationCheckParams(_VerificationCheckRequired, total=False):
    """Params for ``client.verify.verifications.check``. ``code`` is required;
    identify the verification with ``email`` and/or ``phone``."""

    email: str
    phone: str


class _ContactCreateRequired(TypedDict):
    email: str


class ContactCreateParams(_ContactCreateRequired, total=False):
    """Params for ``client.contacts.create``. ``email`` is required."""

    first_name: str
    last_name: str
    external_id: str
    data: Mapping[str, Any]


class ContactUpdateParams(TypedDict, total=False):
    """Params for ``client.contacts.update``. Every key is optional — only the
    fields you pass change."""

    email: str
    first_name: str
    last_name: str
    external_id: str
    data: Mapping[str, Any]


class ContactListParams(TypedDict, total=False):
    """Filters for ``client.contacts.list``. Every key is optional."""

    email: str
    external_id: str
    search: str
    limit: int
    starting_after: str
    ending_before: str


class _ContactBatchRequired(TypedDict):
    contacts: Sequence[Mapping[str, Any]]


class ContactBatchParams(_ContactBatchRequired, total=False):
    """Params for ``client.contacts.batch``. ``contacts`` is required — a sequence
    of per-contact params, each shaped like ``ContactCreateParams``."""

    audience_ids: Sequence[str]
    data_mode: str


class _ContactPropertyCreateRequired(TypedDict):
    key: str
    type: str


class ContactPropertyCreateParams(_ContactPropertyCreateRequired, total=False):
    """Params for ``client.contact_properties.create``. ``key`` and ``type`` are
    required; ``type`` is one of ``"string"``, ``"number"``, ``"boolean"``."""

    fallback_value: Any


class ContactPropertyUpdateParams(TypedDict, total=False):
    """Params for ``client.contact_properties.update``. Every key is optional."""

    fallback_value: Any


class ContactPropertyListParams(TypedDict, total=False):
    """Filters for ``client.contact_properties.list``. Every key is optional."""

    limit: int
    starting_after: str
    ending_before: str


class _AudienceCreateRequired(TypedDict):
    name: str


class AudienceCreateParams(_AudienceCreateRequired, total=False):
    """Params for ``client.audiences.create``. ``name`` is required; an unset
    ``type`` defaults to ``"static"`` on the server."""

    description: str
    type: str


class AudienceUpdateParams(TypedDict, total=False):
    """Params for ``client.audiences.update``. Every key is optional — only the
    fields you pass change."""

    name: str
    description: str


class AudienceListParams(TypedDict, total=False):
    """Filters for ``client.audiences.list``. Every key is optional."""

    limit: int
    starting_after: str
    ending_before: str


class AudienceListContactsParams(TypedDict, total=False):
    """Filters for ``client.audiences.list_contacts``. Every key is optional."""

    limit: int
    starting_after: str
    ending_before: str


class _DomainCreateRequired(TypedDict):
    domain: str


class DomainCreateParams(_DomainCreateRequired, total=False):
    """Params for ``client.domains.create``. ``domain`` is required; the rest
    default server-side when omitted. ``return_path`` and ``tracking`` are the
    name part only (Bird appends the sending domain); ``dkim_mode`` is ``"txt"``
    or ``"delegated"``.
    """

    return_path: str
    tracking: str
    dkim_mode: str
    click_tracking: bool
    open_tracking: bool


class DomainUpdateParams(TypedDict, total=False):
    """Params for ``client.domains.update``. Every key is optional — only the
    fields you pass change. Pass ``tracking=None`` to remove the tracking domain
    (both tracking toggles must be off first, else the API returns 409).
    """

    click_tracking: bool
    open_tracking: bool
    tracking: str | None
    return_path: str
    dkim_mode: str
    inbound_enabled: bool


class DomainListParams(TypedDict, total=False):
    """Filters for ``client.domains.list``. Every key is optional."""

    name: str
    limit: int
    starting_after: str
    ending_before: str


class _AudienceContactsAddRequired(TypedDict):
    contact_ids: Sequence[str]


class AudienceContactsAddParams(_AudienceContactsAddRequired, total=False):
    """Params for ``client.audiences.add_contacts``. ``contact_ids`` is
    required — up to 1,000 existing contact ids."""


class _AudienceContactsRemoveRequired(TypedDict):
    contact_ids: Sequence[str]


class AudienceContactsRemoveParams(_AudienceContactsRemoveRequired, total=False):
    """Params for ``client.audiences.remove_contacts``. ``contact_ids`` is
    required — up to 1,000 existing contact ids."""


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
