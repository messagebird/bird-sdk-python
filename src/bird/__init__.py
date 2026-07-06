"""The official Python SDK for the Bird email platform (ADR-0045).

The wire models are generated from the OpenAPI spec into ``bird._generated`` and
never hand-edited; this package is the hand-written, idiomatic layer on top — a
synchronous ``Bird`` client and an asynchronous ``AsyncBird`` client, a typed
exception hierarchy, safe retries, pagination, and webhook verification.
"""

from __future__ import annotations

from bird._client import AsyncBird, Bird
from bird._response import APIResponse
from bird._types import (
    Attachment,
    EmailDefaults,
    EmailListParams,
    EmailSendBatchParams,
    EmailSendParams,
    RequestOptions,
)
from bird._generated import (
    EmailMessage,
    EmailMessageBatchResponse,
    WebhookEvent,
)
from bird._event_types import WebhookEventType
from bird.resources.webhooks import GenericWebhookEvent
from bird._exceptions import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    BirdError,
    ErrorDetail,
    ErrorNextAction,
    ErrorType,
    RateLimitError,
    ValidationError,
    WebhookVerificationError,
)
from bird.pagination import AsyncPage, SyncPage
from bird._version import __version__

__all__ = [
    "Bird",
    "AsyncBird",
    "RequestOptions",
    "EmailDefaults",
    "Attachment",
    "EmailSendParams",
    "EmailSendBatchParams",
    "EmailListParams",
    "APIResponse",
    "SyncPage",
    "AsyncPage",
    "EmailMessage",
    "EmailMessageBatchResponse",
    "WebhookEvent",
    "GenericWebhookEvent",
    "WebhookEventType",
    "BirdError",
    "APIError",
    "APIStatusError",
    "RateLimitError",
    "ValidationError",
    "APIConnectionError",
    "APITimeoutError",
    "WebhookVerificationError",
    "ErrorDetail",
    "ErrorNextAction",
    "ErrorType",
    "__version__",
]
