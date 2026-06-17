from __future__ import annotations

import json

import httpx
import pytest
import respx

from bird import Bird
from bird._base_client import USER_AGENT
from bird._exceptions import APIError

BASE = "https://eu1.platform.bird.com"
ID1 = "em_01krdgeqcxet5s7t44vh8rt9mg"


def _message() -> dict:
    return {
        "id": ID1, "from": {"email": "a@b.com"}, "to": [{"email": "c@d.com"}], "subject": "Hi",
        "category": "transactional", "status": "accepted",
        "accepted_count": 1, "processed_count": 0, "delivered_count": 0, "bounced_count": 0,
        "complained_count": 0, "deferred_count": 0, "rejected_count": 0,
        "open_count": 0, "click_count": 0, "track_opens": True, "track_clicks": True,
        "created_at": "2026-01-01T00:00:00Z",
    }


def test_user_agent_matches_cross_sdk_prefix() -> None:
    # bird-sdk-go / bird-sdk-js → bird-sdk-python
    assert USER_AGENT.startswith("bird-sdk-python/")


@respx.mock
def test_per_call_max_retries_override() -> None:
    route = respx.get(f"{BASE}/v1/email/messages/{ID1}").mock(return_value=httpx.Response(503))
    # client default is 2 retries; the per-call option drops it to 0 → a single attempt.
    with pytest.raises(APIError):
        Bird(api_key="bk_eu1_s", max_retries=2).email.get(ID1, options={"max_retries": 0})
    assert route.call_count == 1


@respx.mock
def test_email_defaults_fill_unset_fields_and_per_send_wins() -> None:
    route = respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=_message()))
    client = Bird(api_key="bk_eu1_s", email_defaults={"from_": "default@acme.com", "track_opens": False})

    client.email.send(to=["c@d.com"], subject="Hi", text="x")     # no from_ → default fills it
    body = json.loads(route.calls.last.request.content)
    assert body["from"] == "default@acme.com"
    assert body["track_opens"] is False

    client.email.send(from_="override@acme.com", to=["c@d.com"], subject="Hi", text="x")
    body = json.loads(route.calls.last.request.content)
    assert body["from"] == "override@acme.com"                    # per-send value wins
