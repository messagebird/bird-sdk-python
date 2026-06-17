from __future__ import annotations

import httpx
import respx

from bird import Bird
from bird._response import APIResponse

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


@respx.mock
def test_with_raw_response_exposes_metadata_and_parses() -> None:
    respx.post(f"{BASE}/v1/email/messages").mock(
        return_value=httpx.Response(200, json=_message(), headers={"x-request-id": "req_9"})
    )
    raw = Bird(api_key="bk_eu1_secret").email.with_raw_response.send(
        from_="a@b.com", to=["c@d.com"], subject="Hi", text="x"
    )
    assert isinstance(raw, APIResponse)
    assert raw.status_code == 200
    assert raw.request_id == "req_9"
    assert raw.headers["x-request-id"] == "req_9"
    assert raw.parse().id == ID1


@respx.mock
async def test_async_with_raw_response() -> None:
    from bird import AsyncBird

    respx.get(f"{BASE}/v1/email/messages/{ID1}").mock(
        return_value=httpx.Response(200, json=_message(), headers={"x-request-id": "req_a"})
    )
    async with AsyncBird(api_key="bk_eu1_secret") as client:
        raw = await client.email.with_raw_response.get(ID1)
    assert raw.request_id == "req_a"
    assert raw.parse().subject == "Hi"
