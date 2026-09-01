from __future__ import annotations

import httpx
import pytest
import respx

from bird import APIConnectionError, APIStatusError, AsyncBird, Bird, WhatsappMedia
from bird._constants import DEFAULT_TIMEOUT
from bird.resources.whatsapp_messages import _storage_timeout

BASE = "https://eu1.platform.bird.com"
MESSAGE_ID = "wam_01krdgeqcxet5s7t44vh8rt9mg"
MEDIA_ID = "waf_01krdgeqcxet5s7t44vh8rt9mg"
PATH = f"{BASE}/v1/whatsapp/messages/{MESSAGE_ID}/media/{MEDIA_ID}"
STORAGE = "https://storage.test/blob.png?X-Amz-Signature=abc"
PNG = b"\x89PNG\r\n\x1a\n"


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret")


def _redirect(storage: httpx.Response | None = None) -> respx.Route:
    respx.get(PATH).mock(return_value=httpx.Response(302, headers={"Location": STORAGE}))
    return respx.get(STORAGE).mock(
        return_value=storage
        or httpx.Response(200, content=PNG, headers={"Content-Type": "image/png"})
    )


@respx.mock
def test_media_follows_the_redirect() -> None:
    _redirect()
    media = client().whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)
    assert isinstance(media, WhatsappMedia)
    assert media.data == PNG
    assert media.content_type == "image/png"
    assert media.content_length == len(PNG)


# The presigned URL carries its own credential and refuses a second auth
# mechanism, so a Bird header reaching storage is both a leak and a broken
# request. This is the assertion the whole two-leg design exists for.
@respx.mock
def test_media_sends_no_credentials_to_storage() -> None:
    api = respx.get(PATH).mock(return_value=httpx.Response(302, headers={"Location": STORAGE}))
    storage = _redirect()

    client().whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)

    # The API leg must carry the key, or this passes on a client that never
    # authenticates anything.
    assert api.calls.last.request.headers["authorization"] == "Bearer bk_eu1_secret"

    headers = storage.calls.last.request.headers
    assert "authorization" not in headers
    assert not [name for name in headers if name.lower().startswith("bird-")]


# The conformance corpus cannot script a 302 — vector.schema.json's scripted
# responses carry only status and body, no headers — so this is the branch the
# whatsapp.messages.media vector actually drives.
@respx.mock
def test_media_accepts_a_direct_2xx() -> None:
    respx.get(PATH).mock(
        return_value=httpx.Response(200, content=PNG, headers={"Content-Type": "image/png"})
    )
    media = client().whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)
    assert media.data == PNG
    assert media.content_type == "image/png"


@respx.mock
def test_media_falls_back_to_octet_stream() -> None:
    _redirect(httpx.Response(200, content=PNG))
    assert client().whatsapp.messages.media(MESSAGE_ID, MEDIA_ID).content_type == "application/octet-stream"


@respx.mock
def test_media_refused_link_names_the_recovery() -> None:
    _redirect(httpx.Response(403, text="<Error><Code>AccessDenied</Code></Error>"))
    # A storage refusal is not a Bird API failure: mapping it as one would report
    # the caller's own key as lacking permission.
    with pytest.raises(APIConnectionError, match="media again"):
        client().whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)


@respx.mock
def test_media_redirect_without_location() -> None:
    respx.get(PATH).mock(return_value=httpx.Response(302))
    with pytest.raises(APIConnectionError, match="Location"):
        client().whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)


# The API leg keeps the core's error mapping: an expired media object is a Bird
# 410, not a storage failure, and must not be flattened into one.
@respx.mock
def test_media_surfaces_an_api_error() -> None:
    respx.get(PATH).mock(
        return_value=httpx.Response(410, json={"error": {"type": "not_found_error", "code": "E00404"}})
    )
    with pytest.raises(APIStatusError) as excinfo:
        client().whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)
    assert excinfo.value.status_code == 410


@respx.mock
@pytest.mark.asyncio
async def test_async_media_follows_the_redirect() -> None:
    storage = _redirect()
    media = await AsyncBird(api_key="bk_eu1_secret").whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)
    assert media.data == PNG
    assert media.content_type == "image/png"
    assert "authorization" not in storage.calls.last.request.headers


# A transport failure on the storage hop is the same recovery as a refusal, so it
# surfaces as the same error. Without this the caller sees a raw httpx exception,
# the only place this SDK would leak one.
@respx.mock
def test_media_transport_failure_becomes_a_connection_error() -> None:
    respx.get(PATH).mock(return_value=httpx.Response(302, headers={"Location": STORAGE}))
    respx.get(STORAGE).mock(side_effect=httpx.ConnectTimeout("timed out"))
    with pytest.raises(APIConnectionError, match="media again"):
        client().whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)


@respx.mock
@pytest.mark.asyncio
async def test_async_media_transport_failure_becomes_a_connection_error() -> None:
    respx.get(PATH).mock(return_value=httpx.Response(302, headers={"Location": STORAGE}))
    respx.get(STORAGE).mock(side_effect=httpx.ConnectTimeout("timed out"))
    with pytest.raises(APIConnectionError, match="media again"):
        await AsyncBird(api_key="bk_eu1_secret").whatsapp.messages.media(MESSAGE_ID, MEDIA_ID)


# httpx's own default is 5s; a 100 MB video is a normal download here, so the
# storage hop runs on the SDK's timeout, and a per-call override still wins.
def test_storage_hop_timeout_prefers_the_call_then_the_client() -> None:
    assert _storage_timeout(None, DEFAULT_TIMEOUT) is DEFAULT_TIMEOUT
    assert _storage_timeout({"timeout": 5.0}, DEFAULT_TIMEOUT) == 5.0
    assert _storage_timeout({"timeout": None}, DEFAULT_TIMEOUT) is None
    assert client().timeout is DEFAULT_TIMEOUT
