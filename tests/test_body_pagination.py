from __future__ import annotations

import json
from copy import deepcopy

import httpx
import pytest
import respx
from pydantic import BaseModel

from bird import AsyncBird, Bird
from bird.pagination import AsyncPage, SyncPage

BASE = "https://eu1.platform.bird.com"
BODY = {
    "from": "2026-08-01", "to": "2026-08-15", "timezone": "Europe/Amsterdam",
    "metrics": ["delivered"], "group_by": "recipient_domain",
    "filters": {"recipient_domain": {"exclude": ["example.com"]}},
    "ending_before": "backward",
}


class Row(BaseModel):
    value: int


def responses() -> list[httpx.Response]:
    return [
        httpx.Response(200, json={"data": [{"value": 1}], "next_cursor": "next", "period": {"to": "2026-08-15T22:00:00Z"}, "data_as_of": None, "prev_cursor": "previous", "refresh_cursor": "refresh"}),
        httpx.Response(503, headers={"Retry-After": "0"}, json={}),
        httpx.Response(200, json={"data": [{"value": 2}], "next_cursor": None}),
    ]


def assert_requests(route: respx.Route, original: dict) -> None:
    requests = [call.request for call in route.calls]
    expected = {**BODY, "ending_before": "option-backward", "limit": 2}
    assert json.loads(requests[0].content) == expected
    expected.pop("ending_before")
    expected["starting_after"] = "next"
    assert json.loads(requests[1].content) == expected
    assert requests[1].content == requests[2].content
    assert all(request.url.query == b"trace=kept" for request in requests)
    keys = [request.headers["Idempotency-Key"] for request in requests]
    assert keys[0] == "explicit-first-page"
    assert keys[1] != keys[0]
    assert keys[1] == keys[2]
    assert original == BODY


@respx.mock
def test_post_pages_preserve_body_and_retry_each_page() -> None:
    route = respx.post(f"{BASE}/v1/metrics/query").mock(side_effect=responses())
    original = deepcopy(BODY)
    with Bird(api_key="bk_eu1_secret", max_retries=1) as bird:
        page = SyncPage(bird, "/v1/metrics/query", {}, Row, {
            "idempotency_key": "explicit-first-page", "extra_query": {"trace": "kept"},
            "extra_body": {"limit": 2, "ending_before": "option-backward"},
        }, method="POST", body=original)
        assert page.has_next_page()
        assert [row.value for row in page] == [1, 2]
        assert page.response is not None
        assert page.response["period"]["to"] == "2026-08-15T22:00:00Z"
        assert page.response["data_as_of"] is None
        assert page.response["prev_cursor"] == "previous"
        assert page.response["refresh_cursor"] == "refresh"
    assert_requests(route, original)


@respx.mock
@pytest.mark.asyncio
async def test_async_post_pages_preserve_body_and_retry_each_page() -> None:
    route = respx.post(f"{BASE}/v1/metrics/query").mock(side_effect=responses())
    original = deepcopy(BODY)
    async with AsyncBird(api_key="bk_eu1_secret", max_retries=1) as bird:
        page = AsyncPage(bird, "/v1/metrics/query", {}, Row, {
            "idempotency_key": "explicit-first-page", "extra_query": {"trace": "kept"},
            "extra_body": {"limit": 2, "ending_before": "option-backward"},
        }, method="POST", body=original)
        assert (await page).data[0].value == 1
        assert [row.value async for row in page] == [1, 2]
        assert page.response is not None
        assert page.response["period"]["to"] == "2026-08-15T22:00:00Z"
        assert page.response["data_as_of"] is None
    assert_requests(route, original)
