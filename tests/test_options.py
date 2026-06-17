from __future__ import annotations

import json

import httpx
import respx

from bird import Bird

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


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret")


@respx.mock
def test_send_options_forward_header_idempotency_and_extra_body() -> None:
    route = respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=_message()))
    client().email.send(
        from_="a@b.com", to=["c@d.com"], subject="Hi", html="<p>x</p>",
        options={"extra_headers": {"X-Custom": "v"}, "idempotency_key": "key-123",
                 "extra_body": {"x_preview_flag": True}},
    )
    sent = route.calls.last.request
    assert sent.headers["x-custom"] == "v"
    assert sent.headers["idempotency-key"] == "key-123"  # explicit key overrides the auto one
    assert json.loads(sent.content)["x_preview_flag"] is True  # extra_body merged into the wire body


@respx.mock
def test_list_options_forward_to_each_page_request() -> None:
    respx.get(f"{BASE}/v1/email/messages").mock(
        side_effect=[
            httpx.Response(200, json={"data": [_message()], "next_cursor": "c2"}),
            httpx.Response(200, json={"data": [], "next_cursor": None}),
        ]
    )
    pages = list(client().email.list(options={"extra_headers": {"X-Trace": "t"}}))
    assert len(pages) == 1
    calls = respx.calls
    assert all(call.request.headers.get("x-trace") == "t" for call in calls)
    assert len(calls) == 2  # the trace header threads through the auto-paginated second request
