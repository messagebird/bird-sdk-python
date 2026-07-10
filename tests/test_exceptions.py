"""Guards for the hand-maintained error facade (_exceptions).

No generator emits the exception classes, so these tests are the guard that every
ErrorBody wire field is surfaced on the typed error, and that the ADR-0073 recovery
fields (remediation + next) round-trip through from_response.
"""

from __future__ import annotations

import json

import pytest

from bird._exceptions import ErrorNextAction, ValidationError, from_response
from bird._generated import ErrorBody

# Each ErrorBody wire field → the attribute that surfaces it on the exception.
# A new wire field is unmapped here until it is added to _exceptions.py.
WIRE_TO_ATTR = {
    "type": "type",
    "code": "code",
    "name": "name",
    "message": "message",
    "param": "param",
    "doc_url": "doc_url",
    "request_id": "request_id",
    "vendor_code": "vendor_code",
    "details": "details",
    "remediation": "remediation",
    "next": "next",
    "unmet_gates": "unmet_gates",
}


def test_error_body_fields_all_surfaced() -> None:
    """Every generated ErrorBody field maps to a facade attribute."""
    for field in ErrorBody.model_fields:
        assert field in WIRE_TO_ATTR, f"wire field {field!r} is unmapped in _exceptions.py"


def test_from_response_surfaces_recovery() -> None:
    """from_response carries the wire recovery (remediation + next, ADR-0073), and
    the resulting error exposes an attribute for every mapped wire field."""
    body = json.dumps(
        {
            "error": {
                "type": "validation_error",
                "code": "E11005",
                "message": "empty pool",
                "remediation": "Assign a dedicated IP to the pool, then retry.",
                "next": [
                    {
                        "operation": "assignDedicatedIp",
                        "description": "Assign a dedicated IP",
                        "scope": "email:write",
                    }
                ],
            }
        }
    )
    err = from_response(422, body, {})
    assert isinstance(err, ValidationError)
    assert err.remediation == "Assign a dedicated IP to the pool, then retry."
    assert err.next == [
        ErrorNextAction(operation="assignDedicatedIp", description="Assign a dedicated IP", scope="email:write")
    ]
    for attr in WIRE_TO_ATTR.values():
        assert hasattr(err, attr), f"error is missing surfaced attribute {attr!r}"


@pytest.mark.parametrize("next_value", ['"next": null,', ""], ids=["null", "absent"])
def test_from_response_tolerates_null_or_absent_next(next_value: str) -> None:
    """A present-but-null `next` (or an absent one) must not crash from_response —
    `.get("next", [])` returns None on an explicit null, so the comprehension would
    iterate None. `.next` degrades to []."""
    body = '{"error":{"type":"conflict_error","code":"E11003","message":"x",' + next_value + '"remediation":"r"}}'
    err = from_response(409, body, {})
    assert err.next == []
    assert err.remediation == "r"
