"""Subresources of one SMS message: ``client.sms.messages``. The
channel's own message verbs stay on ``client.sms``; this namespace holds
what a single message owns.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from bird._resource import AsyncResource, Resource, _opts
from bird._types import RequestOptions
from bird.resources.whatsapp_messages import (
    _media_location, _storage_timeout, _storage_failed, _storage_refused,
)

_PATH = "/v1/sms/messages"


@dataclass(frozen=True)
class SmsMediaDownload:
    """Media downloaded from a received MMS message. ``content_type`` is
    what storage declared, which is the message's own ``mime_type``."""

    data: bytes
    content_type: str
    content_length: int


def _media_path(message_id: str, media_id: str) -> str:
    return f"{_PATH}/{message_id}/media/{media_id}"


def _media_from(response: httpx.Response) -> SmsMediaDownload:
    data = response.content
    return SmsMediaDownload(
        data=data,
        content_type=response.headers.get("Content-Type") or "application/octet-stream",
        content_length=len(data),
    )


class SmsMessages(Resource):
    """One message's subresources. Reach it via ``client.sms.messages``."""

    def media(
        self, message_id: str, media_id: str, options: RequestOptions | None = None
    ) -> SmsMediaDownload:
        """Download the media on a received MMS message: an image, video,
        audio clip or document. ``media_id`` is the ``id`` on the
        message's media entry, which ``client.sms.get`` returns.

        Media expires with its message, 30 days after it arrives, and this
        raises a 404 :class:`APIStatusError` from then on. A 410 means only the
        file expired: the message still lists the media's ``mime_type`` and
        ``filename``. Messages sent through Bird carry no stored media.

        ```python
        media = client.sms.messages.media(
            "sms_01kya19eknftrs2s6p82asmvnh", "smf_01kyb2m4xq7whs0d8n3prv6tez"
        )
        print(media.content_type, media.content_length)
        ```
        """
        response = self._client.request(
            "GET", _media_path(message_id, media_id), success_status=302, **_opts(options)
        )
        # A 2xx is an edge answering with the bytes directly, which is also the
        # only arm the conformance corpus can script — its responses carry only
        # status and body, so no 302 with a Location.
        if response.status_code != 302:
            return _media_from(response)
        location = _media_location(response)
        try:
            with httpx.Client(timeout=_storage_timeout(options, self._client.timeout)) as bare:
                stored = bare.get(location)
        except httpx.HTTPError as err:
            raise _storage_failed(err) from err
        if not stored.is_success:
            raise _storage_refused(stored.status_code)
        return _media_from(stored)


class AsyncSmsMessages(AsyncResource):
    """Async mirror of `SmsMessages`."""

    async def media(
        self, message_id: str, media_id: str, options: RequestOptions | None = None
    ) -> SmsMediaDownload:
        """Download a received message's media; see :meth:`SmsMessages.media`."""
        response = await self._client.request(
            "GET", _media_path(message_id, media_id), success_status=302, **_opts(options)
        )
        if response.status_code != 302:
            return _media_from(response)
        location = _media_location(response)
        try:
            async with httpx.AsyncClient(
                timeout=_storage_timeout(options, self._client.timeout)
            ) as bare:
                stored = await bare.get(location)
        except httpx.HTTPError as err:
            raise _storage_failed(err) from err
        if not stored.is_success:
            raise _storage_refused(stored.status_code)
        return _media_from(stored)
