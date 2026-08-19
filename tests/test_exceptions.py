"""Guards for the hand-maintained error facade (_exceptions).

No generator emits the exception classes, so these tests are the guard that every
ErrorBody wire field is surfaced on the typed error, and that the ADR-0073 recovery
fields (remediation + next) round-trip through from_response.
"""

from __future__ import annotations

import json

import pytest

from bird._exceptions import NextAction, ValidationError, from_response
from bird._generated import ErrorBody
from bird._generated import NextAction as WireNextAction

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
}


def test_error_body_fields_all_surfaced() -> None:
    """Every generated ErrorBody field maps to a facade attribute."""
    for field in ErrorBody.model_fields:
        assert field in WIRE_TO_ATTR, f"wire field {field!r} is unmapped in _exceptions.py"


def test_next_action_fields_all_surfaced() -> None:
    """The same guard one level down: every generated NextAction field is on the
    facade dataclass. The ErrorBody guard above sees `next` only as a whole, so a
    field added inside a step passes it unnoticed — which is how `kind`, `params`
    and `url` were dropped for a release."""
    facade = set(NextAction.__dataclass_fields__)
    for field in WireNextAction.model_fields:
        assert field in facade, f"wire field {field!r} of NextAction is unmapped in _exceptions.py"


def test_from_response_surfaces_recovery() -> None:
    """from_response carries the wire recovery (remediation + next, ADR-0073/0124), and
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
                        "kind": "operation",
                        "operation": "assignDedicatedIp",
                        "description": "Assign a dedicated IP",
                        "params": {"pool_id": "pool_123"},
                    }
                ],
            }
        }
    )
    err = from_response(422, body, {})
    assert isinstance(err, ValidationError)
    assert err.remediation == "Assign a dedicated IP to the pool, then retry."
    assert err.next == [
        NextAction(
            kind="operation",
            description="Assign a dedicated IP",
            operation="assignDedicatedIp",
            params={"pool_id": "pool_123"},
        )
    ]
    for attr in WIRE_TO_ATTR.values():
        assert hasattr(err, attr), f"error is missing surfaced attribute {attr!r}"


def test_from_response_leaves_an_op_less_step_without_an_operation() -> None:
    """A step whose kind is not `operation` carries no operation, and must arrive with
    `operation` as None — an empty string reads as an operationId the caller can call."""
    body = json.dumps(
        {
            "error": {
                "type": "precondition_error",
                "code": "E01028",
                "message": "domain not verified",
                "next": [
                    {
                        "kind": "external",
                        "description": "Publish the DKIM record at your DNS provider",
                        "url": "https://example.test/dns",
                    },
                    {"kind": "wait", "description": "Verification is in progress; read again shortly"},
                ],
            }
        }
    )
    err = from_response(412, body, {})
    external, wait = err.next
    assert external.operation is None
    assert external.url == "https://example.test/dns"
    assert wait.operation is None
    assert wait.params is None
    assert wait.url is None


@pytest.mark.parametrize("next_value", ['"next": null,', ""], ids=["null", "absent"])
def test_from_response_tolerates_null_or_absent_next(next_value: str) -> None:
    """A present-but-null `next` (or an absent one) must not crash from_response —
    `.get("next", [])` returns None on an explicit null, so the comprehension would
    iterate None. `.next` degrades to []."""
    body = '{"error":{"type":"conflict_error","code":"E01028","message":"x",' + next_value + '"remediation":"r"}}'
    err = from_response(409, body, {})
    assert err.next == []
    assert err.remediation == "r"
