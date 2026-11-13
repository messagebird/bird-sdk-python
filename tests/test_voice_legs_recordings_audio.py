from __future__ import annotations

import httpx
import pytest
import respx

from bird import APIConnectionError, APIStatusError, AsyncBird, Bird, ErrorType, VoiceRecordingAudio

BASE = "https://eu1.platform.bird.com"
LEG_ID = "vcl_01krdgeqcxet5s7t44vh8rt9mg"
RECORDING_ID = "vrc_01krdgeqcxet5s7t44vh8rt9mg"
PATH = f"{BASE}/v1/voice/legs/{LEG_ID}/recordings/{RECORDING_ID}/audio"
STORAGE = "https://storage.test/recording.wav?X-Amz-Signature=abc"
WAV = b"RIFF"


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret")


def _redirect(storage: httpx.Response | None = None) -> tuple[respx.Route, respx.Route]:
    api = respx.get(PATH).mock(return_value=httpx.Response(302, headers={"Location": STORAGE}))
    stored = respx.get(STORAGE).mock(
        return_value=storage
        or httpx.Response(200, content=WAV, headers={"Content-Type": "audio/wav"})
    )
    return api, stored


# The presigned URL carries its own credential and refuses a second auth
# mechanism, so a Bird header reaching storage is both a leak and a broken
# request.
@respx.mock
def test_audio_follows_the_redirect_without_credentials() -> None:
    api, storage = _redirect()

    audio = client().voice.legs.recordings.audio(LEG_ID, RECORDING_ID)

    assert isinstance(audio, VoiceRecordingAudio)
    assert (audio.data, audio.content_type, audio.content_length) == (WAV, "audio/wav", len(WAV))
    assert api.calls.last.request.headers["authorization"] == "Bearer bk_eu1_secret"
    headers = storage.calls.last.request.headers
    assert "authorization" not in headers
    assert not [name for name in headers if name.lower().startswith("bird-")]


# The conformance corpus cannot script a 302, so this is the branch the
# voice.legs.recordings.audio vector actually drives.
@respx.mock
def test_audio_accepts_a_direct_2xx() -> None:
    respx.get(PATH).mock(
        return_value=httpx.Response(200, content=WAV, headers={"Content-Type": "audio/wav"})
    )
    assert client().voice.legs.recordings.audio(LEG_ID, RECORDING_ID).data == WAV


@respx.mock
def test_audio_refused_link_names_the_recovery() -> None:
    _redirect(httpx.Response(403, content=b"<Error><Code>AccessDenied</Code></Error>"))
    with pytest.raises(APIConnectionError, match="audio again"):
        client().voice.legs.recordings.audio(LEG_ID, RECORDING_ID)


# A leg that is still recording is the API's own 425, which the caller needs as
# an API error to tell "wait" from "gone".
@respx.mock
def test_audio_surfaces_still_recording() -> None:
    respx.get(PATH).mock(
        return_value=httpx.Response(
            425, json={"error": {"type": "too_early_error", "code": "E21083"}}
        )
    )
    with pytest.raises(APIStatusError) as excinfo:
        client().voice.legs.recordings.audio(LEG_ID, RECORDING_ID)
    assert excinfo.value.status_code == 425
    assert ErrorType(excinfo.value.type) is ErrorType.too_early


@respx.mock
@pytest.mark.asyncio
async def test_async_audio_follows_the_redirect_without_credentials() -> None:
    _, storage = _redirect()
    audio = await AsyncBird(api_key="bk_eu1_secret").voice.legs.recordings.audio(
        LEG_ID, RECORDING_ID
    )
    assert audio.data == WAV
    assert "authorization" not in storage.calls.last.request.headers


def _assert_storage_saw_no_credentials(storage: respx.Route) -> None:
    headers = storage.calls.last.request.headers
    assert "authorization" not in headers
    assert not [name for name in headers if name.lower().startswith(("bird-", "x-workspace-id"))]


# A caller's own http_client may follow redirects; the API leg must still stop
# at the 302 so the storage leg goes out bare.
@respx.mock
def test_audio_stops_at_the_redirect_on_a_following_http_client() -> None:
    _, storage = _redirect()
    http_client = httpx.Client(follow_redirects=True, headers={"X-Workspace-Id": "ws_1"})
    bird = Bird(api_key="bk_eu1_secret", http_client=http_client)

    assert bird.voice.legs.recordings.audio(LEG_ID, RECORDING_ID).data == WAV
    _assert_storage_saw_no_credentials(storage)


@respx.mock
def test_audio_refused_link_on_a_following_http_client_names_the_recovery() -> None:
    _redirect(httpx.Response(403, content=b"<Error><Code>AccessDenied</Code></Error>"))
    bird = Bird(api_key="bk_eu1_secret", http_client=httpx.Client(follow_redirects=True))
    with pytest.raises(APIConnectionError, match="audio again"):
        bird.voice.legs.recordings.audio(LEG_ID, RECORDING_ID)


@respx.mock
@pytest.mark.asyncio
async def test_async_audio_stops_at_the_redirect_on_a_following_http_client() -> None:
    _, storage = _redirect()
    http_client = httpx.AsyncClient(follow_redirects=True, headers={"X-Workspace-Id": "ws_1"})
    bird = AsyncBird(api_key="bk_eu1_secret", http_client=http_client)

    assert (await bird.voice.legs.recordings.audio(LEG_ID, RECORDING_ID)).data == WAV
    _assert_storage_saw_no_credentials(storage)


@respx.mock
@pytest.mark.asyncio
async def test_async_audio_refused_link_on_a_following_http_client_names_the_recovery() -> None:
    _redirect(httpx.Response(403, content=b"<Error><Code>AccessDenied</Code></Error>"))
    bird = AsyncBird(api_key="bk_eu1_secret", http_client=httpx.AsyncClient(follow_redirects=True))
    with pytest.raises(APIConnectionError, match="audio again"):
        await bird.voice.legs.recordings.audio(LEG_ID, RECORDING_ID)
