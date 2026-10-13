"""Conformance drivers discard decoded responses."""

from __future__ import annotations

import httpx
import respx

from bird import Bird

BASE = "https://eu1.platform.bird.com"
AID = "adn_01krdgeqcxet5s7t44vh8rt201"


@respx.mock
def test_membership_keeps_unavailable_distinct_from_zero() -> None:
    respx.get(f"{BASE}/v1/audiences/{AID}/membership").mock(
        side_effect=[
            httpx.Response(200, json={}),
            httpx.Response(200, json={"membership": {"total": 0, "data_as_of": "2026-10-12T09:41:07.512843Z"}}),
        ]
    )
    client = Bird(api_key="bk_eu1_secret")

    unavailable = client.audiences.membership(AID)
    assert unavailable.membership is None
    assert "membership" not in unavailable.model_fields_set

    empty = client.audiences.membership(AID).membership
    assert empty is not None
    assert empty.total == 0
    assert empty.data_as_of == "2026-10-12T09:41:07.512843Z"
