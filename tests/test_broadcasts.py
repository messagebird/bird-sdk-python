from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import respx

from bird import Bird, BirdError, BroadcastCreateParams, EmailBroadcast

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
        "scheduled_at": datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc),
    }
    client().broadcasts.create(**params)
    body = json.loads(route.calls.last.request.content)
    assert body["from"] == "newsletter@acme.com"
    assert body["scheduled_at"] == "2026-08-01T09:00:00Z"
