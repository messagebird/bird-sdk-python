from __future__ import annotations

import inspect
import json
from typing import Any

import httpx
import pytest
from pydantic import Field, create_model

from bird import AsyncBird, Bird, BirdError
from bird._generated import ContactCreateRequest
from bird._models import BaseModel, to_wire
from bird._types import omit
from bird.resources import contacts_gen


# Existing optional nonnullable keyword arguments keep None as omission. The
# generated contacts case owns the generic path; nullable fields differ below.
CASES = [
    ("contacts.create", (), {}, "first_name", "Jane"),
    ("amb.send", (), {"from_": "b52d6267-2b62-4f8a-8842-0533d0f1dc07", "to": "customer", "text": {"body": "Hello"}}, "category", "transactional"),
    ("email.send", (), {"from_": "sender@example.com", "to": ["to@example.com"], "text": "Hello"}, "subject", "Hello"),
    ("email.send", (), {"from_": "sender@example.com", "to": ["to@example.com"], "template": "welcome", "language": None, "parameters": None}, "metadata", {"source": "signup"}),
    ("email.with_raw_response.send", (), {"from_": "sender@example.com", "to": ["to@example.com"], "text": "Hello"}, "subject", "Hello"),
    ("email.templates.create", (), {"slug": "welcome", "category": "marketing", "source": "html"}, "name", "Welcome"),
    ("preferences.create", (), {"channel": "email", "handle": "to@example.com", "status": "granted"}, "source", "signup"),
    ("webhooks.create", (), {"events": ["email.delivered"], "url": "https://example.com/webhook"}, "description", "Deliveries"),
    ("broadcasts.create", (), {}, "category", "marketing"),
    ("broadcasts.update", ("eb_01krdgeqcxet5s7t44vh8rt9mg",), {}, "category", "marketing"),
    ("broadcasts.send", ("eb_01krdgeqcxet5s7t44vh8rt9mg",), {}, "scheduled_at", "2026-12-01T09:00:00Z"),
    ("email.mailboxes.messages.create", ("mbx_01krdgeqcxet5s7t44vh8rt9mg",), {"to": [{"email": "to@example.com"}], "subject": "Hello"}, "text", "Hello"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("path,args,base,field,value", CASES, ids=[case[0] for case in CASES])
async def test_public_request_omission_value_and_compatible_none(
    asynchronous: bool, path: str, args: tuple[str, ...], base: dict[str, Any], field: str, value: Any,
) -> None:
    bodies: list[dict[str, Any]] = []

    def record(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        # A terminal API error lets this test inspect requests independently of
        # response model fixtures; response decoding has separate owners.
        return httpx.Response(400, json={"type": "validation_error", "message": "recorded"})

    transport = httpx.MockTransport(record)
    http_client: Any = httpx.AsyncClient(transport=transport) if asynchronous else httpx.Client(transport=transport)
    client: Any = (AsyncBird if asynchronous else Bird)(api_key="bk_eu1_test", http_client=http_client, max_retries=0)
    method: Any = client
    for segment in path.split("."):
        method = getattr(method, segment)
    try:
        for supplied in ({}, {field: value}, {field: None}):
            with pytest.raises(BirdError):
                result = method(*args, **base, **supplied)
                if inspect.isawaitable(result):
                    await result
        assert len(bodies) == 3
        assert field not in bodies[0]
        assert bodies[1][field] == value
        assert field not in bodies[2]
        if base.get("template") == "welcome":
            assert bodies[0]["template"] == {"slug": "welcome"}
    finally:
        if asynchronous:
            await http_client.aclose()
        else:
            http_client.close()


class NestedPresence(BaseModel):
    required_null: str | None
    nullable: str | None = None
    nonnullable: str | None = Field(default=None, json_schema_extra={"x-bird-nullable": False})


class ContainerPresence(BaseModel):
    child: NestedPresence
    children: list[NestedPresence]
    by_name: dict[str, NestedPresence]


ContactPresenceRequest = create_model(
    "ContactPresenceRequest", __base__=ContactCreateRequest, data=(ContainerPresence, ...),
)


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_new_nested_model_fields_keep_all_states_through_public_facade(
    monkeypatch: pytest.MonkeyPatch, asynchronous: bool,
) -> None:
    # Substitute the wire model to model a newly generated nested property;
    # keep the actual public facade, request validation and transport intact.
    monkeypatch.setattr(contacts_gen, "ContactCreateRequest", ContactPresenceRequest)
    child: dict[str, Any] = {"required_null": None}
    data: dict[str, Any] = {}
    bodies: list[dict[str, Any]] = []

    def record(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(400, json={"type": "validation_error", "message": "recorded"})

    transport = httpx.MockTransport(record)
    http_client: Any = httpx.AsyncClient(transport=transport) if asynchronous else httpx.Client(transport=transport)
    client: Any = (AsyncBird if asynchronous else Bird)(api_key="bk_eu1_test", http_client=http_client, max_retries=0)
    try:
        expected = []
        for fields in ({}, {"nullable": "value"}, {"nullable": None}):
            child = {"required_null": None, **fields}
            data = {"child": child, "children": [child], "by_name": {"one": child}}
            with pytest.raises(BirdError):
                result = client.contacts.create(data=data)
                if inspect.isawaitable(result):
                    await result
            expected.append({"data": data})
        assert bodies == expected
        for field in ("child", "children", "by_name"):
            invalid = {**child, "nonnullable": None}
            replacement = invalid if field == "child" else [invalid] if field == "children" else {"one": invalid}
            changed = {**data, field: replacement}
            with pytest.raises(BirdError, match="nonnullable: null is not allowed"):
                result = client.contacts.create(data=changed)
                if inspect.isawaitable(result):
                    await result
        assert len(bodies) == 3
    finally:
        if asynchronous:
            await http_client.aclose()
        else:
            http_client.close()


def test_required_nullable_and_response_compatibility() -> None:
    assert to_wire(NestedPresence, {"required_null": None, "nullable": omit}) == {"required_null": None}
    with pytest.raises(BirdError, match="required_null"):
        to_wire(NestedPresence, {})
    # The extra request rule must not make an absent response property required,
    # or reject the permissive None the SDK already accepts while decoding.
    assert NestedPresence(required_null=None, nonnullable=None).nonnullable is None


def test_root_none_omission_uses_field_metadata_and_aliases() -> None:
    class Request(BaseModel):
        renamed: str | None = Field(default=None, alias="wire_name", json_schema_extra={"x-bird-nullable": False})
        clearable: str | None = None

    assert to_wire(Request, {"wire_name": None, "clearable": None}) == {"clearable": None}
    assert to_wire(Request, {"renamed": None}) == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_batch_preserves_omission_and_rejects_explicit_nested_null(asynchronous: bool) -> None:
    bodies: list[dict[str, Any]] = []

    def record(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(400, json={"type": "validation_error", "message": "recorded"})

    transport = httpx.MockTransport(record)
    http_client: Any = httpx.AsyncClient(transport=transport) if asynchronous else httpx.Client(transport=transport)
    client: Any = (AsyncBird if asynchronous else Bird)(api_key="bk_eu1_test", http_client=http_client, max_retries=0)
    message = {"from_": "sender@example.com", "to": ["to@example.com"], "text": "Hello"}
    try:
        with pytest.raises(BirdError):
            result = client.email.send_batch(messages=[message, {**message, "subject": "Hello"}])
            if inspect.isawaitable(result):
                await result
        assert len(bodies) == 1
        assert "subject" not in bodies[0]["messages"][0]
        assert bodies[0]["messages"][1]["subject"] == "Hello"
        with pytest.raises(BirdError, match="subject: null is not allowed"):
            result = client.email.send_batch(messages=[{**message, "subject": None}])
            if inspect.isawaitable(result):
                await result
        assert len(bodies) == 1
    finally:
        if asynchronous:
            await http_client.aclose()
        else:
            http_client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_nullable_property_and_unconstrained_map_nulls_reach_transport(asynchronous: bool) -> None:
    bodies: list[dict[str, Any]] = []

    def record(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(400, json={"type": "validation_error", "message": "recorded"})

    transport = httpx.MockTransport(record)
    http_client: Any = httpx.AsyncClient(transport=transport) if asynchronous else httpx.Client(transport=transport)
    client: Any = (AsyncBird if asynchronous else Bird)(api_key="bk_eu1_test", http_client=http_client, max_retries=0)
    data = {"clear": None, "nested": {"clear": None}, "items": [None, {"clear": None}]}
    try:
        expected = [{}, {"first_name": "Jane"}, {"first_name": None, "data": data}]
        for supplied in expected:
            with pytest.raises(BirdError):
                result = client.contacts.update("con_01krdgeqcxet5s7t44vh8rt9mg", **supplied)
                if inspect.isawaitable(result):
                    await result
        assert bodies == expected
    finally:
        if asynchronous:
            await http_client.aclose()
        else:
            http_client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_voice_route_required_nullable_through_recording_transport(asynchronous: bool) -> None:
    bodies: list[dict[str, Any]] = []

    def record(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(400, json={"type": "validation_error", "message": "recorded"})

    transport = httpx.MockTransport(record)
    http_client: Any = httpx.AsyncClient(transport=transport) if asynchronous else httpx.Client(transport=transport)
    client: Any = (AsyncBird if asynchronous else Bird)(api_key="bk_eu1_test", http_client=http_client, max_retries=2)
    try:
        with pytest.raises(BirdError, match="route"):
            result = client.voice.numbers.update("number-id", inbound_configuration={})
            if inspect.isawaitable(result):
                await result
        assert bodies == []
        for route in (None, {"type": "reject"}):
            with pytest.raises(BirdError):
                result = client.voice.numbers.update("number-id", inbound_configuration={"route": route})
                if inspect.isawaitable(result):
                    await result
        assert bodies == [{"inbound_configuration": {"route": None}}, {"inbound_configuration": {"route": {"type": "reject"}}}]
    finally:
        if asynchronous:
            await http_client.aclose()
        else:
            http_client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("path", ["email.send", "email.with_raw_response.send", "email.send_batch"])
async def test_email_omitted_optional_fields_are_not_fabricated_nulls(asynchronous: bool, path: str) -> None:
    bodies: list[dict[str, Any]] = []

    def record(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(400, json={"type": "validation_error", "message": "recorded"})

    transport = httpx.MockTransport(record)
    http_client: Any = httpx.AsyncClient(transport=transport) if asynchronous else httpx.Client(transport=transport)
    client: Any = (AsyncBird if asynchronous else Bird)(api_key="bk_eu1_test", http_client=http_client, max_retries=0)
    message = {"from_": "sender@example.com", "to": ["to@example.com"], "text": "Hello"}
    method: Any = client
    for segment in path.split("."):
        method = getattr(method, segment)
    try:
        with pytest.raises(BirdError):
            result = method(messages=[message]) if path.endswith("send_batch") else method(**message)
            if inspect.isawaitable(result):
                await result
        assert len(bodies) == 1
        body = bodies[0]["messages"][0] if path.endswith("send_batch") else bodies[0]
        assert body == {"from": "sender@example.com", "to": ["to@example.com"], "text": "Hello"}
    finally:
        if asynchronous:
            await http_client.aclose()
        else:
            http_client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("path,args,base,field,pointer", [
    ("contact_properties.create", (), {"key": "plan", "type": "string"}, "fallback_value", ("fallback_value",)),
    ("contact_properties.update", ("prp_01krdgeqcxet5s7t44vh8rt9mg",), {}, "fallback_value", ("fallback_value",)),
    ("realtime.publish", ("rap_01krdgeqcxet5s7t44vh8rt9mg",), {"event": "changed", "channels": ["orders"]}, "data", ("data",)),
    ("realtime.publish_batch", ("rap_01krdgeqcxet5s7t44vh8rt9mg",), {}, "data", ("events", 0, "data")),
    ("realtime.members.send", ("rap_01krdgeqcxet5s7t44vh8rt9mg", "customer"), {"event": "changed"}, "data", ("data",)),
])
async def test_explicitly_nullable_untyped_fields_cross_public_facades(
    asynchronous: bool, path: str, args: tuple[str, ...], base: dict[str, Any],
    field: str, pointer: tuple[Any, ...],
) -> None:
    bodies: list[dict[str, Any]] = []

    def record(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(400, json={"type": "validation_error", "message": "recorded"})

    transport = httpx.MockTransport(record)
    http_client: Any = httpx.AsyncClient(transport=transport) if asynchronous else httpx.Client(transport=transport)
    client: Any = (AsyncBird if asynchronous else Bird)(
        api_key="bk_eu1_test", http_client=http_client, max_retries=0,
        realtime_key="rk_test", realtime_secret="rs_test",
    )
    method: Any = client
    for segment in path.split("."):
        method = getattr(method, segment)
    try:
        for supplied in ({}, {field: None}, {field: "value"}):
            kwargs = {**base, **supplied}
            if path == "realtime.publish_batch":
                kwargs = {"events": [{"event": "changed", "channel": "orders", **supplied}]}
            with pytest.raises(BirdError):
                result = method(*args, **kwargs)
                if inspect.isawaitable(result):
                    await result
        assert len(bodies) == 3
        for index, body in enumerate(bodies):
            parent: Any = body
            for segment in pointer[:-1]:
                parent = parent[segment]
            if index == 0:
                assert pointer[-1] not in parent
            else:
                assert parent[pointer[-1]] == (None if index == 1 else "value")
    finally:
        if asynchronous:
            await http_client.aclose()
        else:
            http_client.close()
