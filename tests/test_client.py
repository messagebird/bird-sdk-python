from __future__ import annotations

import httpx
import pytest
import respx

from bird import AsyncBird, Bird, BirdError

BASE = "https://eu1.platform.bird.com"


def test_region_inferred_from_key_prefix() -> None:
    assert Bird(api_key="bk_eu1_secret").base_url == BASE


def test_explicit_region_overrides_inference() -> None:
    assert Bird(api_key="bk_eu1_secret", region="us1").base_url == "https://us1.platform.bird.com"


def test_base_url_wins_over_region() -> None:
    client = Bird(api_key="bk_eu1_secret", region="us1", base_url="https://custom.example.com")
    assert client.base_url == "https://custom.example.com"


def test_api_key_and_region_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIRD_API_KEY", "bk_us1_fromenv")
    monkeypatch.delenv("BIRD_BASE_URL", raising=False)
    client = Bird()
    assert client.api_key == "bk_us1_fromenv"
    assert client.base_url == "https://us1.platform.bird.com"


def test_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BIRD_API_KEY", raising=False)
    with pytest.raises(BirdError):
        Bird()


def test_unresolvable_region_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BIRD_BASE_URL", raising=False)
    with pytest.raises(BirdError):
        Bird(api_key="plainkey_without_region_prefix")


@respx.mock
def test_verb_get_decodes_json() -> None:
    respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(200, json={"a": 1}))
    assert Bird(api_key="bk_eu1_s").get("/v1/x") == {"a": 1}


@respx.mock
def test_verb_post_casts_to_model() -> None:
    from bird import EmailMessage

    message = {
        "id": "em_01krdgeqcxet5s7t44vh8rt9mg", "from": {"email": "a@b.com"}, "to": [{"email": "c@d.com"}], "subject": "Hi",
        "category": "transactional", "status": "accepted",
        "accepted_count": 1, "processed_count": 0, "delivered_count": 0, "bounced_count": 0,
        "complained_count": 0, "deferred_count": 0, "rejected_count": 0,
        "open_count": 0, "click_count": 0, "track_opens": True, "track_clicks": True,
        "created_at": "2026-01-01T00:00:00Z",
    }
    respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=message))
    out = Bird(api_key="bk_eu1_s").post("/v1/email/messages", body={"subject": "Hi"}, cast_to=EmailMessage)
    assert isinstance(out, EmailMessage)
    assert out.subject == "Hi"


def test_with_options_overrides_and_keeps_the_rest() -> None:
    client = Bird(api_key="bk_eu1_s", max_retries=2)
    derived = client.with_options(max_retries=5)
    assert derived.max_retries == 5
    assert derived.api_key == client.api_key
    assert derived.base_url == client.base_url


def test_with_options_shares_http_client_and_does_not_close_it() -> None:
    client = Bird(api_key="bk_eu1_s")
    derived = client.with_options(max_retries=5)
    assert derived._client is client._client  # shares the parent's connection pool
    assert derived._owns_client is False
    derived.close()  # a no-op: the derived client must not close the shared pool
    assert not client._client.is_closed


def test_with_options_region_override_rederives_base_url() -> None:
    client = Bird(api_key="bk_eu1_s")
    assert client.with_options(region="us1").base_url == "https://us1.platform.bird.com"


def test_with_options_region_override_drops_inherited_base_url() -> None:
    # A region override must re-derive the URL, not inherit the parent's explicit base_url.
    client = Bird(api_key="bk_eu1_s", base_url="https://custom.example.com")
    assert client.with_options(region="us1").base_url == "https://us1.platform.bird.com"


def test_with_options_api_key_override_rederives_base_url() -> None:
    # A new regional key must re-resolve the endpoint, not keep the parent's host.
    client = Bird(api_key="bk_eu1_s")
    assert client.base_url == "https://eu1.platform.bird.com"
    assert client.with_options(api_key="bk_us1_s").base_url == "https://us1.platform.bird.com"


def test_with_options_api_key_override_preserves_explicit_region() -> None:
    # An explicit region (overriding the key prefix) must survive key rotation —
    # region is persisted in _config, so it isn't lost when base_url re-resolves.
    client = Bird(api_key="bk_eu1_s", region="us1")
    assert client.base_url == "https://us1.platform.bird.com"
    assert client.with_options(api_key="bk_eu1_other").base_url == "https://us1.platform.bird.com"


async def test_async_with_options_shares_http_client_and_does_not_close_it() -> None:
    client = AsyncBird(api_key="bk_eu1_s")
    derived = client.with_options(max_retries=5)
    assert derived._client is client._client
    assert derived._owns_client is False
    await derived.close()  # a no-op: must not close the shared pool
    assert not client._client.is_closed
    await client.close()


@respx.mock
async def test_async_verb_get() -> None:
    respx.get(f"{BASE}/v1/x").mock(return_value=httpx.Response(200, json={"ok": True}))
    async with AsyncBird(api_key="bk_eu1_s") as client:
        assert await client.get("/v1/x") == {"ok": True}
