"""Open-enum fields narrow to the enum member without closing the enum.

The forward-compatibility half is the one that matters: a bare ``Enum`` field
raises on a value the enum does not list, so a new server event type would break
every client. ``Union[Enum, str]`` in left-to-right mode keeps the field open.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bird._generated import (
    VerificationChannel,
    VerificationChannelEntry,
    WhatsAppError,
    WhatsAppErrorCode,
)


def test_known_value_is_the_enum_member() -> None:
    entry = VerificationChannelEntry(channel="sms")
    assert entry.channel is VerificationChannel.sms
    # str-subclass, so comparing against the wire string still works and no
    # existing consumer has to learn the enum.
    assert entry.channel == "sms"


def test_unknown_value_still_decodes() -> None:
    """A value no version of this SDK knows must not raise."""
    entry = VerificationChannelEntry(channel="telepathy")
    assert entry.channel == "telepathy"
    assert not isinstance(entry.channel, VerificationChannel)


def test_both_round_trip_to_the_wire_value() -> None:
    assert VerificationChannelEntry(channel="sms").model_dump(mode="json") == {
        "channel": "sms"
    }
    assert VerificationChannelEntry(channel="telepathy").model_dump(mode="json") == {
        "channel": "telepathy"
    }


def test_known_values_are_enumerable() -> None:
    assert [c.value for c in VerificationChannel] == ["email", "sms", "whatsapp", "telegram"]


def _whatsapp_error(code: str) -> WhatsAppError:
    return WhatsAppError(
        code=code,
        description="Message could not be delivered.",
        occurred_at="2026-07-31T12:00:00Z",
    )


def test_open_enum_holds_across_schemas() -> None:
    """Not just the one field: every retyped enum keeps both properties."""
    assert _whatsapp_error("rate_limited").code is WhatsAppErrorCode.rate_limited
    assert _whatsapp_error("invented_in_2030").code == "invented_in_2030"


def test_a_genuinely_closed_enum_still_rejects() -> None:
    """The retype is scoped to open enums; a closed one must keep validating."""
    with pytest.raises(ValidationError):
        VerificationChannelEntry(channel=object())  # type: ignore[arg-type]
