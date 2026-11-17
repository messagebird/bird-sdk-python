import pytest
import respx

from bird import AsyncBird, Bird, SmsMediaDownload

PATH = "https://eu1.platform.bird.com/v1/sms/messages/sms_1/media/smf_1"
STORAGE = "https://storage.test/photo"


@respx.mock
def test_sms_media_download() -> None:
    api = respx.get(PATH).respond(302, headers={"Location": STORAGE})
    storage = respx.get(STORAGE).respond(200, content=b"photo", headers={"Content-Type": "image/jpeg"})
    media = Bird(api_key="bk_eu1_secret").sms.messages.media("sms_1", "smf_1")
    assert isinstance(media, SmsMediaDownload)
    assert (media.data, media.content_type, media.content_length) == (b"photo", "image/jpeg", 5)
    assert api.calls.last.request.headers["authorization"] == "Bearer bk_eu1_secret"
    assert "authorization" not in storage.calls.last.request.headers
    assert not [name for name in storage.calls.last.request.headers if name.lower().startswith("bird-")]


@respx.mock
@pytest.mark.asyncio
async def test_async_sms_media_download() -> None:
    api = respx.get(PATH).respond(302, headers={"Location": STORAGE})
    storage = respx.get(STORAGE).respond(200, content=b"photo", headers={"Content-Type": "image/jpeg"})
    media = await AsyncBird(api_key="bk_eu1_secret").sms.messages.media("sms_1", "smf_1")
    assert (media.data, media.content_type, media.content_length) == (b"photo", "image/jpeg", 5)
    assert api.calls.last.request.headers["authorization"] == "Bearer bk_eu1_secret"
    assert "authorization" not in storage.calls.last.request.headers
    assert not [name for name in storage.calls.last.request.headers if name.lower().startswith("bird-")]
