"""Open-enum fields narrow to the enum member without closing the enum.

The forward-compatibility half is the one that matters: a bare ``Enum`` field
raises on a value the enum does not list, so a new server event type would break
every client. ``Union[Enum, str]`` in left-to-right mode keeps the field open.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from pydantic import ValidationError

from bird import _generated
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


def _unions(node: object, path: str) -> Iterator[tuple[str, dict[str, Any]]]:
    """Every `union` node in a core schema, with the path that reached it."""
    if isinstance(node, dict):
        if node.get("type") == "union":
            yield path, node
        for key, val in node.items():
            yield from _unions(val, f"{path}/{key}")
    elif isinstance(node, (list, tuple)):
        for i, val in enumerate(node):
            yield from _unions(val, f"{path}[{i}]")


def _kinds(node: dict[str, Any]) -> list[str | None]:
    """The union's branch types, in the order pydantic will try them."""
    choices = [c[0] if isinstance(c, tuple) else c for c in node.get("choices", [])]
    return [c.get("type") for c in choices if isinstance(c, dict)]


def _is_open(kinds: list[str | None]) -> bool:
    """An open enum's union: the enum's known values, and a bare string."""
    return "enum" in kinds and "str" in kinds


def _narrows(node: dict[str, Any], kinds: list[str | None]) -> bool:
    """Left to right AND enum-first. Either alone hands back a plain string:
    smart mode prefers the looser branch, and str-first matches everything.
    """
    return node.get("mode") == "left_to_right" and kinds.index("enum") < kinds.index("str")


def test_every_open_enum_reference_prefers_the_member() -> None:
    """Exhaustive, because the fields above are the ones a test happens to name.

    A reference that stops narrowing is silent: the field still decodes, it just
    yields `str` where the enum member was promised. The mode rides on the union
    itself, which is what makes it survive inside a `List[...]`.
    """
    loose = []
    seen = 0
    for name in dir(_generated):
        model = getattr(_generated, name)
        schema = getattr(model, "__pydantic_core_schema__", None)
        if not isinstance(model, type) or schema is None:
            continue
        for path, node in _unions(schema, name):
            kinds = _kinds(node)
            if not _is_open(kinds):
                continue
            seen += 1
            if not _narrows(node, kinds):
                loose.append(f"{path} (mode={node.get('mode')}, {kinds})")
    assert not loose, f"{len(loose)} open-enum reference(s) do not narrow: {loose[:10]}"
    # A walk that matched nothing would pass over an empty input.
    assert seen > 0, "no open-enum unions in the generated models at all"
