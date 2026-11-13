"""The recordings of one leg: ``client.voice.legs.recordings``."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx

from bird._exceptions import APIConnectionError
from bird._resource import AsyncResource, Resource, _opts
from bird._types import RequestOptions
# The storage leg is the one WhatsApp media takes, so both downloads keep the
# client's credentials off it the same way.
from bird.resources.whatsapp_messages import _storage_failed, _storage_refused, _storage_timeout


@dataclass(frozen=True)
class VoiceRecordingAudio:
    """The downloaded audio of one recording. ``content_type`` is what storage
    declared, ``audio/wav``."""

    data: bytes
    content_type: str
    content_length: int


def _audio_path(leg_id: str, recording_id: str) -> str:
    leg, recording = quote(leg_id, safe=""), quote(recording_id, safe="")
    return f"/v1/voice/legs/{leg}/recordings/{recording}/audio"


def _audio_from(response: httpx.Response) -> VoiceRecordingAudio:
    data = response.content
    return VoiceRecordingAudio(
        data=data,
        content_type=response.headers.get("Content-Type") or "application/octet-stream",
        content_length=len(data),
    )


def _audio_location(response: httpx.Response) -> str:
    location = response.headers.get("Location")
    if not location:
        raise APIConnectionError("recording redirect carried no Location header")
    return location


class VoiceLegsRecordings(Resource):
    """One leg's recordings. Reach it via ``client.voice.legs.recordings``."""

    def audio(
        self, leg_id: str, recording_id: str, options: RequestOptions | None = None
    ) -> VoiceRecordingAudio:
        """Download one recording as a WAV file. ``leg_id`` and ``recording_id``
        are the ``leg_id`` and ``id`` of an entry in ``recordings``, which
        ``client.voice.calls.recordings.list`` returns.

        A 425 :class:`APIStatusError` means the leg is still recording: call
        again in a few seconds. A 404 means the capture failed, or the
        recording is older than 30 days.

        ```python
        audio = client.voice.legs.recordings.audio(
            "vcl_01krdgeqcxet5s7t44vh8rt9mg", "vrc_01krdgeqcxet5s7t44vh8rt9mg"
        )
        print(audio.content_type, audio.content_length)
        ```
        """
        response = self._client.request(
            "GET", _audio_path(leg_id, recording_id), success_status=302, **_opts(options)
        )
        # A 2xx is an edge answering with the bytes directly, which is also the
        # only arm the conformance corpus can script: its responses carry only
        # status and body, so no 302 with a Location.
        if response.status_code != 302:
            return _audio_from(response)
        location = _audio_location(response)
        try:
            with httpx.Client(timeout=_storage_timeout(options, self._client.timeout)) as bare:
                stored = bare.get(location)
        except httpx.HTTPError as err:
            raise _storage_failed(err, "audio") from err
        if not stored.is_success:
            raise _storage_refused(stored.status_code, "audio")
        return _audio_from(stored)


class AsyncVoiceLegsRecordings(AsyncResource):
    """Async mirror of `VoiceLegsRecordings`."""

    async def audio(
        self, leg_id: str, recording_id: str, options: RequestOptions | None = None
    ) -> VoiceRecordingAudio:
        """Download one recording; see :meth:`VoiceLegsRecordings.audio`."""
        response = await self._client.request(
            "GET", _audio_path(leg_id, recording_id), success_status=302, **_opts(options)
        )
        if response.status_code != 302:
            return _audio_from(response)
        location = _audio_location(response)
        try:
            async with httpx.AsyncClient(
                timeout=_storage_timeout(options, self._client.timeout)
            ) as bare:
                stored = await bare.get(location)
        except httpx.HTTPError as err:
            raise _storage_failed(err, "audio") from err
        if not stored.is_success:
            raise _storage_refused(stored.status_code, "audio")
        return _audio_from(stored)
