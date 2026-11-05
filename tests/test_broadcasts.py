from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest
import respx

from bird import (
    AsyncBird,
    Bird,
    BirdError,
    BroadcastCreateParams,
    BroadcastUpdateParams,
    EmailBroadcast,
    EmailBroadcastTemplateUpdate,
    omit,
)

BASE = "https://eu1.platform.bird.com"
ID1 = "eb_01krdgeqcxet5s7t44vh8rt9mg"


def _broadcast() -> dict:
    return {
        "id": ID1, "category": "marketing", "status": "scheduled", "recipient_count": 0,
        "track_opens": True, "track_clicks": True,
        "created_at": "2026-01-01T00:00:00Z", "sent_at": None,
    }


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret")


@respx.mock
def test_send_writes_an_aware_datetime_as_a_bare_z() -> None:
    route = respx.post(f"{BASE}/v1/email/broadcasts/{ID1}/send").mock(
        return_value=httpx.Response(202, json=_broadcast())
    )
    broadcast = client().broadcasts.send(
        ID1, scheduled_at=datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc)
    )
    assert isinstance(broadcast, EmailBroadcast)
    body = json.loads(route.calls.last.request.content)
    # The other three SDKs and the conformance vector write a zero offset this way.
    assert body["scheduled_at"] == "2026-08-01T09:00:00Z"


@respx.mock
def test_send_keeps_a_non_zero_offset_as_written() -> None:
    route = respx.post(f"{BASE}/v1/email/broadcasts/{ID1}/send").mock(
        return_value=httpx.Response(202, json=_broadcast())
    )
    client().broadcasts.send(
        ID1, scheduled_at=datetime(2026, 8, 1, 9, 0, tzinfo=timezone(timedelta(hours=2)))
    )
    body = json.loads(route.calls.last.request.content)
    assert body["scheduled_at"] == "2026-08-01T09:00:00+02:00"


@respx.mock
def test_create_writes_an_aware_datetime_the_same_way() -> None:
    route = respx.post(f"{BASE}/v1/email/broadcasts").mock(
        return_value=httpx.Response(200, json=_broadcast())
    )
    client().broadcasts.create(
        from_="newsletter@acme.com",
        audience_id="adn_01krdgeqcxet5s7t44vh8rt9mg",
        template="emt_01krdgeqcxet5s7t44vh8rt9mg",
        send=True,
        scheduled_at=datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc),
    )
    body = json.loads(route.calls.last.request.content)
    assert body["scheduled_at"] == "2026-08-01T09:00:00Z"


@respx.mock
def test_send_passes_a_callers_own_string_through() -> None:
    route = respx.post(f"{BASE}/v1/email/broadcasts/{ID1}/send").mock(
        return_value=httpx.Response(202, json=_broadcast())
    )
    client().broadcasts.send(ID1, scheduled_at="2026-08-01T09:00:00Z")
    body = json.loads(route.calls.last.request.content)
    assert body["scheduled_at"] == "2026-08-01T09:00:00Z"


def test_send_refuses_a_naive_datetime_before_sending() -> None:
    with respx.mock:
        route = respx.post(f"{BASE}/v1/email/broadcasts/{ID1}/send")
        with pytest.raises(BirdError, match="timezone-aware"):
            client().broadcasts.send(ID1, scheduled_at=datetime(2026, 8, 1, 9, 0))
        assert not route.called


def test_create_refuses_a_naive_datetime_before_sending() -> None:
    with respx.mock:
        route = respx.post(f"{BASE}/v1/email/broadcasts")
        with pytest.raises(BirdError, match="timezone-aware"):
            client().broadcasts.create(
                audience_id="adn_01krdgeqcxet5s7t44vh8rt9mg",
                scheduled_at=datetime(2026, 8, 1, 9, 0),
            )
        assert not route.called


@respx.mock
def test_create_takes_a_params_dict_splatted() -> None:
    route = respx.post(f"{BASE}/v1/email/broadcasts").mock(
        return_value=httpx.Response(200, json=_broadcast())
    )
    params: BroadcastCreateParams = {
        "from_": "newsletter@acme.com",
        "audience_id": "adn_01krdgeqcxet5s7t44vh8rt9mg",
        "template": "emt_01krdgeqcxet5s7t44vh8rt9mg",
        "language": "nl",
        "parameters": None,
        "scheduled_at": datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc),
    }
    client().broadcasts.create(**params)
    body = json.loads(route.calls.last.request.content)
    assert body["from"] == "newsletter@acme.com"
    assert body["template"] == {"id": "emt_01krdgeqcxet5s7t44vh8rt9mg", "language": "nl"}
    assert body["scheduled_at"] == "2026-08-01T09:00:00Z"


@respx.mock
def test_update_takes_a_params_dict_splatted() -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}").mock(
        return_value=httpx.Response(200, json=_broadcast())
    )
    params: BroadcastUpdateParams = {
        "template": EmailBroadcastTemplateUpdate(id="emt_01krdgeqcxet5s7t44vh8rt9mg", language=None),
    }
    client().broadcasts.update(ID1, **params)
    body = json.loads(route.calls.last.request.content)
    assert body["template"] == {"id": "emt_01krdgeqcxet5s7t44vh8rt9mg", "language": None}


@respx.mock
def test_update_sends_parameter_overrides_without_releasing_the_version() -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}").mock(
        return_value=httpx.Response(200, json=_broadcast())
    )
    client().broadcasts.update(ID1, template=EmailBroadcastTemplateUpdate(
        parameter_overrides={"it": {"count": 9007199254740995, "empty": ""}, "es": {}},
    ))
    body = json.loads(route.calls.last.request.content)
    assert body["template"] == {"parameter_overrides": {"it": {"count": 9007199254740995, "empty": ""}, "es": {}}}


@pytest.mark.parametrize("overrides", [{"it": None}, {"it": []}, None])
def test_create_refuses_a_null_or_non_object_override_map(overrides: Any) -> None:
    with respx.mock:
        route = respx.route(url__regex=rf"{BASE}/v1/email/broadcasts.*")
        if overrides is None:
            route.mock(return_value=httpx.Response(200, json=_broadcast()))
            client().broadcasts.create(template="emt_01krdgeqcxet5s7t44vh8rt9mg", parameter_overrides=None)
            assert "parameter_overrides" not in json.loads(route.calls.last.request.content).get("template", {})
            return
        with pytest.raises(BirdError, match="template.parameter_overrides"):
            client().broadcasts.create(template="emt_01krdgeqcxet5s7t44vh8rt9mg", parameter_overrides=overrides)
        assert not route.called


@pytest.mark.parametrize("template, body", [
    (omit, {}),
    (None, {"template": None}),
    (EmailBroadcastTemplateUpdate(), {"template": {}}),
    (EmailBroadcastTemplateUpdate(language=None), {"template": {"language": None}}),
    (EmailBroadcastTemplateUpdate(parameters={}), {"template": {"parameters": {}}}),
    (EmailBroadcastTemplateUpdate(parameter_overrides={}), {"template": {"parameter_overrides": {}}}),
    (EmailBroadcastTemplateUpdate(parameters={"greeting": None, "count": 9007199254740995}),
     {"template": {"parameters": {"greeting": None, "count": 9007199254740995}}}),
    (EmailBroadcastTemplateUpdate(parameter_overrides={"it": {"greeting": None}, "es": {}}),
     {"template": {"parameter_overrides": {"it": {"greeting": None}, "es": {}}}}),
])
@respx.mock
@pytest.mark.asyncio
async def test_update_typed_template_states_sync_and_async(template: Any, body: dict[str, Any]) -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}").mock(
        return_value=httpx.Response(200, json=_broadcast())
    )
    with client() as synchronous:
        synchronous.broadcasts.update(ID1, template=template, category=None)
    async with AsyncBird(api_key="bk_eu1_secret") as asynchronous:
        await asynchronous.broadcasts.update(ID1, template=template, category=None)
    assert len(route.calls) == 2
    for call in route.calls:
        assert json.loads(call.request.content) == body


@pytest.mark.parametrize("field", ["id", "parameters", "parameter_overrides"])
@respx.mock
@pytest.mark.asyncio
async def test_update_rejects_nested_nonnullable_nulls(field: str) -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}")
    template = EmailBroadcastTemplateUpdate.model_validate({field: None})
    with client() as synchronous:
        with pytest.raises(BirdError, match=rf"template\.{field}: null"):
            synchronous.broadcasts.update(ID1, template=template)
    async with AsyncBird(api_key="bk_eu1_secret") as asynchronous:
        with pytest.raises(BirdError, match=rf"template\.{field}: null"):
            await asynchronous.broadcasts.update(ID1, template=template)
    assert not route.called


@pytest.mark.parametrize("template", ["emt_01krdgeqcxet5s7t44vh8rt9mg", {}, {"language": None}])
@respx.mock
@pytest.mark.asyncio
async def test_update_requires_a_template_model(template: Any) -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}")
    with client() as synchronous:
        with pytest.raises(BirdError, match="EmailBroadcastTemplateUpdate"):
            synchronous.broadcasts.update(ID1, template=template)
    async with AsyncBird(api_key="bk_eu1_secret") as asynchronous:
        with pytest.raises(BirdError, match="EmailBroadcastTemplateUpdate"):
            await asynchronous.broadcasts.update(ID1, template=template)
    assert not route.called


@pytest.mark.parametrize("field, value", [("language", "nl"), ("parameters", {}), ("parameter_overrides", {})])
@respx.mock
@pytest.mark.asyncio
async def test_update_removed_flat_template_keywords(field: str, value: Any) -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}")
    kwargs: dict[str, Any] = {field: value}
    with client() as synchronous:
        with pytest.raises(TypeError, match=field):
            synchronous.broadcasts.update(ID1, **kwargs)
    async with AsyncBird(api_key="bk_eu1_secret") as asynchronous:
        with pytest.raises(TypeError, match=field):
            await asynchronous.broadcasts.update(ID1, **kwargs)
    assert not route.called


@pytest.mark.asyncio
async def test_parameter_operations_refuse_null_parameters_before_sending() -> None:
    with respx.mock:
        route = respx.post(url__regex=rf"{BASE}/v1/email/broadcasts/{ID1}/(validate|preview|test)").mock(
            side_effect=AssertionError("invalid body reached transport")
        )
        async with AsyncBird(api_key="bk_eu1_secret") as asynchronous:
            synchronous = client()
            for operation in ("validate", "preview", "test"):
                fields: dict[str, Any] = {"template": {"parameters": None}}
                if operation == "test":
                    fields.update(to="member@acme.com", preview_fingerprint="preview")
                with pytest.raises(BirdError, match="template.parameters"):
                    getattr(synchronous.broadcasts, operation)(ID1, **fields)
                with pytest.raises(BirdError, match="template.parameters"):
                    await getattr(asynchronous.broadcasts, operation)(ID1, **fields)
                assert not route.called
            synchronous.close()


@pytest.mark.parametrize("options", [None, {"idempotency_key": ""}])
@respx.mock
@pytest.mark.asyncio
async def test_member_test_requires_caller_intent_key(options: Any) -> None:
    route = respx.post(f"{BASE}/v1/email/broadcasts/{ID1}/test").mock(
        return_value=httpx.Response(202, json={
            "id": "em_01krdgeqcxet5s7t44vh8rt9mg", "from": {"email": "sender@example.com"},
            "to": [{"email": "member@example.com"}], "subject": "Member test", "category": "transactional",
            "status": "accepted", "track_opens": False, "track_clicks": False,
            "created_at": "2026-10-03T12:34:56.123Z", "accepted_count": 1,
            "processed_count": 0, "delivered_count": 0, "bounced_count": 0, "complained_count": 0,
            "deferred_count": 0, "rejected_count": 0, "open_count": 0, "click_count": 0,
        })
    )
    with pytest.raises(BirdError, match="idempotency"):
        client().broadcasts.test(ID1, to="member@example.com", preview_fingerprint="matching", options=options)
    assert not route.called
    async with AsyncBird(api_key="bk_eu1_secret") as async_client:
        with pytest.raises(BirdError, match="idempotency"):
            await async_client.broadcasts.test(ID1, to="member@example.com", preview_fingerprint="matching", options=options)
    assert not route.called
