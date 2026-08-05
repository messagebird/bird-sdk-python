from __future__ import annotations

import json

import httpx
import pytest
import respx

from bird import AsyncBird, Bird, BirdError, RealtimeChannelInfo

BASE = "https://eu1.platform.bird.com"
APP = "rap_01krdgeqcxet5s7t44vh8rt9mg"
APP_BASE = f"{BASE}/v1/realtime/apps/{APP}"


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret", realtime_key="rk_test", realtime_secret="rs_test")


def _async_client() -> AsyncBird:
    return AsyncBird(api_key="bk_eu1_secret", realtime_key="rk_test", realtime_secret="rs_test")


@respx.mock
def test_publish_sends_credentials_and_omits_unset_fields() -> None:
    route = respx.post(f"{APP_BASE}/events").mock(return_value=httpx.Response(200, json={}))
    client().realtime.publish(APP, event="greeting", channels=["orders"], data={"hello": "world"})

    sent = route.calls.last.request
    assert sent.headers["X-Realtime-Key"] == "rk_test"
    assert sent.headers["X-Realtime-Secret"] == "rs_test"
    assert json.loads(sent.content) == {
        "event": "greeting", "channels": ["orders"], "data": {"hello": "world"}
    }


@respx.mock
def test_publish_passes_exclude_connection_id_and_include_verbatim() -> None:
    route = respx.post(f"{APP_BASE}/events").mock(return_value=httpx.Response(200, json={}))
    client().realtime.publish(
        APP,
        event="greeting",
        channels=["orders", "presence-lobby"],
        data="plain-string payload",
        exclude_connection_id="81721.1907241",
        include=["connection_count"],
    )
    assert json.loads(route.calls.last.request.content) == {
        "event": "greeting",
        "channels": ["orders", "presence-lobby"],
        "data": "plain-string payload",
        "exclude_connection_id": "81721.1907241",
        "include": ["connection_count"],
    }


@respx.mock
def test_empty_exclude_connection_id_is_rejected_client_side() -> None:
    route = respx.post(f"{APP_BASE}/events").mock(return_value=httpx.Response(200, json={}))
    with pytest.raises(BirdError, match="exclude_connection_id"):
        client().realtime.publish(APP, event="greeting", channels=["orders"], exclude_connection_id="")
    assert route.call_count == 0


@respx.mock
def test_publish_batch_sends_events_array_in_order() -> None:
    route = respx.post(f"{APP_BASE}/batch-events").mock(return_value=httpx.Response(200, json={}))
    client().realtime.publish_batch(
        APP,
        events=[
            {"event": "created", "channel": "orders", "data": {"id": 1}},
            {"event": "updated", "channel": "orders", "data": {"id": 2},
             "exclude_connection_id": "81721.1907241"},
        ],
    )
    assert json.loads(route.calls.last.request.content) == {
        "events": [
            {"event": "created", "channel": "orders", "data": {"id": 1}},
            {"event": "updated", "channel": "orders", "data": {"id": 2},
             "exclude_connection_id": "81721.1907241"},
        ]
    }


@respx.mock
def test_channels_list_is_a_snapshot_not_a_page() -> None:
    route = respx.get(f"{APP_BASE}/channels").mock(
        return_value=httpx.Response(200, json={"data": [{"name": "presence-lobby", "member_count": 3}]})
    )
    channels = client().realtime.channels.list(APP, prefix="presence-", include=["member_count"])

    assert [c.name for c in channels.data] == ["presence-lobby"]
    url = route.calls.last.request.url
    assert url.params["prefix"] == "presence-"
    assert url.params.get_list("include") == ["member_count"]


@respx.mock
def test_channels_get_puts_the_name_in_the_path() -> None:
    respx.get(f"{APP_BASE}/channels/presence-lobby").mock(
        return_value=httpx.Response(200, json={"occupied": True, "member_count": 2})
    )
    channel = client().realtime.channels.get(APP, "presence-lobby", include=["member_count"])
    assert isinstance(channel, RealtimeChannelInfo)
    assert channel.occupied is True
    assert channel.member_count == 2


@respx.mock
def test_channel_members_returns_member_ids() -> None:
    respx.get(f"{APP_BASE}/channels/presence-lobby/members").mock(
        return_value=httpx.Response(200, json={"members": [{"member_id": "m_1"}, {"member_id": "m_2"}]})
    )
    members = client().realtime.channels.members(APP, "presence-lobby")
    assert [m.member_id for m in members.members] == ["m_1", "m_2"]


@respx.mock
def test_member_send_posts_the_event_to_the_members_events_path() -> None:
    route = respx.post(f"{APP_BASE}/members/m_1/events").mock(return_value=httpx.Response(204))
    assert (
        client().realtime.members.send(APP, "m_1", event="order-shipped", data={"id": 42})
        is None
    )
    # The member is the address: no channel is named, because the reserved channel
    # the edge delivers on is built server-side.
    assert json.loads(route.calls.last.request.content) == {
        "event": "order-shipped",
        "data": {"id": 42},
    }


@respx.mock
def test_member_send_omits_data_when_absent() -> None:
    route = respx.post(f"{APP_BASE}/members/m_1/events").mock(return_value=httpx.Response(204))
    client().realtime.members.send(APP, "m_1", event="session-revoked")
    assert json.loads(route.calls.last.request.content) == {"event": "session-revoked"}


@respx.mock
def test_member_disconnect_is_a_bodyless_post_returning_none() -> None:
    route = respx.post(f"{APP_BASE}/members/m_1/disconnect").mock(return_value=httpx.Response(204))
    assert client().realtime.members.disconnect(APP, "m_1") is None
    assert not route.calls.last.request.content


@respx.mock
def test_unknown_response_fields_are_tolerated() -> None:
    respx.get(f"{APP_BASE}/channels/orders").mock(
        return_value=httpx.Response(200, json={"occupied": True, "future_field": "x"})
    )
    channel = client().realtime.channels.get(APP, "orders")
    assert channel.occupied is True


@respx.mock
def test_caller_options_thread_through_but_cannot_override_the_credentials() -> None:
    route = respx.get(f"{APP_BASE}/channels").mock(return_value=httpx.Response(200, json={"data": []}))
    client().realtime.channels.list(
        APP, options={"extra_headers": {"X-Realtime-Key": "attacker", "X-Trace": "abc"}}
    )
    sent = route.calls.last.request
    assert sent.headers["X-Realtime-Key"] == "rk_test"
    assert sent.headers["X-Trace"] == "abc"


@respx.mock
def test_missing_credentials_raises_before_any_request() -> None:
    route = respx.post(f"{APP_BASE}/events").mock(return_value=httpx.Response(200, json={}))
    bird = Bird(api_key="bk_eu1_secret")  # no realtime_key/realtime_secret

    with pytest.raises(BirdError, match="Realtime app credentials"):
        bird.realtime.publish(APP, event="greeting", channels=["orders"])
    with pytest.raises(BirdError, match="Realtime app credentials"):
        bird.realtime.channels.list(APP)
    assert route.call_count == 0


def test_with_options_carries_the_realtime_credentials() -> None:
    derived = client().with_options(max_retries=0)
    assert derived.realtime._auth._key == "rk_test"
    assert derived.realtime._auth._secret == "rs_test"


@respx.mock
async def test_async_surface_mirrors_sync() -> None:
    respx.post(f"{APP_BASE}/events").mock(return_value=httpx.Response(200, json={}))
    respx.get(f"{APP_BASE}/channels/presence-lobby").mock(
        return_value=httpx.Response(200, json={"occupied": True})
    )
    disconnect = respx.post(f"{APP_BASE}/members/m_1/disconnect").mock(return_value=httpx.Response(204))

    async with _async_client() as bird:
        await bird.realtime.publish(APP, event="greeting", channels=["orders"])
        channel = await bird.realtime.channels.get(APP, "presence-lobby")
        assert await bird.realtime.members.disconnect(APP, "m_1") is None

    assert channel.occupied is True
    assert disconnect.called


@respx.mock
async def test_async_missing_credentials_raises_before_any_request() -> None:
    route = respx.post(f"{APP_BASE}/events").mock(return_value=httpx.Response(200, json={}))
    async with AsyncBird(api_key="bk_eu1_secret") as bird:
        with pytest.raises(BirdError, match="Realtime app credentials"):
            await bird.realtime.publish(APP, event="greeting", channels=["orders"])
    assert route.call_count == 0
