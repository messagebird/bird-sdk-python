from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest
import respx

from bird import AsyncBird, Bird, BirdError, BroadcastCreateParams, BroadcastUpdateParams, EmailBroadcast

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
    params: BroadcastUpdateParams = {"template": "emt_01krdgeqcxet5s7t44vh8rt9mg", "language": None, "parameters": None}
    client().broadcasts.update(ID1, **params)
    body = json.loads(route.calls.last.request.content)
    assert body["template"] == {"id": "emt_01krdgeqcxet5s7t44vh8rt9mg", "language": None}


@respx.mock
def test_update_sends_parameter_overrides_without_releasing_the_version() -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}").mock(
        return_value=httpx.Response(200, json=_broadcast())
    )
    client().broadcasts.update(ID1, parameter_overrides={"it": {"count": 9007199254740995, "empty": ""}, "es": {}})
    body = json.loads(route.calls.last.request.content)
    assert body["template"] == {"parameter_overrides": {"it": {"count": 9007199254740995, "empty": ""}, "es": {}}}
    with pytest.raises(ValueError, match="cleared template"):
        client().broadcasts.update(ID1, template=None, parameter_overrides={})


@pytest.mark.parametrize("overrides", [{"it": None}, {"it": []}, None])
def test_create_and_update_refuse_a_null_or_non_object_override_map(overrides: Any) -> None:
    with respx.mock:
        route = respx.route(url__regex=rf"{BASE}/v1/email/broadcasts.*")
        if overrides is None:
            # Outer None keeps the documented omission convention.
            route.mock(return_value=httpx.Response(200, json=_broadcast()))
            client().broadcasts.update(ID1, parameter_overrides=None)
            assert "parameter_overrides" not in json.loads(route.calls.last.request.content).get("template", {})
            return
        with pytest.raises(BirdError, match="template.parameter_overrides"):
            client().broadcasts.update(ID1, parameter_overrides=overrides)
        with pytest.raises(BirdError, match="template.parameter_overrides"):
            client().broadcasts.create(template="emt_01krdgeqcxet5s7t44vh8rt9mg", parameter_overrides=overrides)
        assert not route.called


@respx.mock
def test_scalar_null_inside_a_language_stays_null() -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}").mock(return_value=httpx.Response(200, json=_broadcast()))
    client().broadcasts.update(ID1, parameter_overrides={"it": {"greeting": None}})
    assert json.loads(route.calls.last.request.content)["template"]["parameter_overrides"] == {"it": {"greeting": None}}


def test_update_refuses_a_language_when_the_template_is_cleared() -> None:
    with respx.mock:
        route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}")
        with pytest.raises(ValueError, match="language needs a template"):
            client().broadcasts.update(ID1, template=None, language="nl")
        assert not route.called


@respx.mock
def test_update_clears_template_and_language_together() -> None:
    route = respx.patch(f"{BASE}/v1/email/broadcasts/{ID1}").mock(
        return_value=httpx.Response(200, json=_broadcast())
    )
    client().broadcasts.update(ID1, template=None, language=None)
    body = json.loads(route.calls.last.request.content)
    assert body["template"] is None


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
