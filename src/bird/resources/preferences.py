"""client.preferences — the generated list/get facade plus the two writes the
generator can't derive a body or a return type for: ``create`` assembles
``consented_at`` from a native datetime, and ``delete`` answers 200 with a
``PreferenceWriteResult`` rather than 204, because a delete is itself a
statement that can be refused (a newer statement already on file survives
it) — a ``None``-returning delete would read that refusal as success.
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from bird._exceptions import BirdError
from bird._generated import PreferenceIndividualCreate, PreferenceWriteResult
from bird._models import to_wire
from bird._types import Omit, RequestOptions, omit
from bird.resources.preferences_gen import AsyncPreferencesBase, PreferencesBase

_NAIVE_CONSENTED_AT = (
    "consented_at requires a timezone-aware datetime (e.g. tzinfo=timezone.utc): "
    "the API orders a grant against a stored opt-out by this instant, so an "
    "offset-less value has no defined meaning on the wire"
)


def _consented_at_wire(value: str | datetime | None) -> str | None:
    """RFC 3339 with an explicit offset. A string is already wire-shaped and
    passes through verbatim; a naive ``datetime`` (no ``tzinfo``) is rejected
    rather than silently assumed to be UTC."""
    if not isinstance(value, datetime):
        return value
    if value.utcoffset() is None:
        raise BirdError(_NAIVE_CONSENTED_AT)
    return value.isoformat()


class Preferences(PreferencesBase):
    """The workspace's stated messaging preferences: consent grants and
    opt-outs keyed by channel + handle (+ optional sender scope). Reach it via
    ``client.preferences``."""

    def create(
        self,
        *,
        channel: str,
        handle: str,
        status: str,
        brand_id: str | None | Omit = omit,
        coverage: str | None = None,
        sender_scope: str | None = None,
        source: str | None = None,
        consented_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> PreferenceWriteResult:
        """Record one preference statement for a handle. Writing is an upsert
        keyed by channel + handle (+ ``sender_scope`` and email Brand). A ``201``
        means a live record was created; ``200`` covers updates and refusals.
        Ordering and complaint protection can return ``applied: false``.
        Inspect ``preference`` alongside ``applied``: a newer opt-out or deletion
        returns ``applied: false`` with the revoked preference or ``None``,
        even when consent history is retained.
        Granting over a stored opt-out needs a ``consented_at``
        later than the opt-out. Only this individual operation can clear an email
        Brand complaint with newer consent; bulk writes and imports cannot.
        ``source`` can describe how you collected consent. Other
        opt-outs and delivery blocks still apply.

        ```python
        from datetime import datetime, timezone

        result = client.preferences.create(
            channel="email",
            handle="recipient@example.com",
            status="granted",
            consented_at=datetime.now(timezone.utc),
            source="signup-form-v2",
        )
        print(result.applied, result.preference.id if result.preference else None)
        ```
        """
        body = to_wire(
            PreferenceIndividualCreate,
            {
                "channel": channel,
                "handle": handle,
                "status": status,
                "coverage": coverage,
                "sender_scope": sender_scope,
                "source": source,
                "consented_at": _consented_at_wire(consented_at),
                "brand_id": brand_id,
            },
        )
        return self._write("POST", "/v1/preferences", body, PreferenceWriteResult, options)

    def delete(
        self,
        preference_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> PreferenceWriteResult:
        """Delete a preference, returning its key to having no record.
        Answers ``200`` with the write result rather than ``204``: the delete
        is ordered like any other statement, so ``applied: false`` means a
        newer statement survived it — returned in ``preference`` — rather
        than the key being cleared. Recipient-origin opt-outs and active Brand
        complaints cannot be deleted this way (``422 E25005``). Only individual
        opt-in with newer consent can clear a Brand complaint.

        ```python
        result = client.preferences.delete("prf_01krdgeqcxet5s7t44vh8rt9mg")
        if not result.applied:
            print("refused, current statement:", result.preference.status)
        ```
        """
        return self._action(
            "DELETE",
            f"/v1/preferences/{quote(preference_id, safe='')}",
            PreferenceWriteResult,
            options,
        )


class AsyncPreferences(AsyncPreferencesBase):
    """Async mirror of `Preferences`."""

    async def create(
        self,
        *,
        channel: str,
        handle: str,
        status: str,
        brand_id: str | None | Omit = omit,
        coverage: str | None = None,
        sender_scope: str | None = None,
        source: str | None = None,
        consented_at: str | datetime | None = None,
        options: RequestOptions | None = None,
    ) -> PreferenceWriteResult:
        """Record one preference statement. See `Preferences.create`."""
        body = to_wire(
            PreferenceIndividualCreate,
            {
                "channel": channel,
                "handle": handle,
                "status": status,
                "coverage": coverage,
                "sender_scope": sender_scope,
                "source": source,
                "consented_at": _consented_at_wire(consented_at),
                "brand_id": brand_id,
            },
        )
        return await self._write("POST", "/v1/preferences", body, PreferenceWriteResult, options)

    async def delete(
        self,
        preference_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> PreferenceWriteResult:
        """Delete a preference. See `Preferences.delete`."""
        return await self._action(
            "DELETE",
            f"/v1/preferences/{quote(preference_id, safe='')}",
            PreferenceWriteResult,
            options,
        )
