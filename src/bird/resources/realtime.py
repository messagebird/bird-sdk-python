"""The Realtime channel: ``client.realtime`` — publish events to connected clients
and inspect the live channel/presence state of a Realtime app.

Every Realtime operation is scoped to one Realtime app and authenticated with that
app's own credentials, sent as the ``X-Realtime-Key``/``X-Realtime-Secret`` headers
alongside the workspace bearer token. Configure them once on the client
(``Bird(realtime_key=..., realtime_secret=...)``); a call made without them raises
``BirdError`` before any request is sent.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._exceptions import BirdError
from bird._generated import (
    RealtimeBatchPublish,
    RealtimeBatchPublishResult,
    RealtimeChannelInfo,
    RealtimeChannelMembers,
    RealtimeChannelsList,
    RealtimeMemberPublish,
    RealtimePublish,
    RealtimePublishResult,
)
from bird._models import to_wire
from bird._types import RealtimeBatchEventParams, RequestOptions

_BASE = "/v1/realtime/apps"


def _app_path(realtime_app_id: str, *suffix: str) -> str:
    return "/".join((_BASE, realtime_app_id, *suffix))


def _publish_body(
    *,
    event: str,
    channels: Sequence[str],
    data: Any,
    exclude_connection_id: str | None,
    include: Sequence[str] | None,
) -> dict[str, Any]:
    return to_wire(RealtimePublish, {
        "event": event,
        "channels": list(channels),
        "data": data,
        "exclude_connection_id": exclude_connection_id,
        "include": list(include) if include else None,
    })


def _member_send_body(*, event: str, data: Any) -> dict[str, Any]:
    return to_wire(RealtimeMemberPublish, {"event": event, "data": data})


def _batch_body(events: Sequence[RealtimeBatchEventParams]) -> dict[str, Any]:
    return to_wire(RealtimeBatchPublish, {"events": [dict(event) for event in events]})


class _RealtimeAuth:
    """Holds the Realtime app credentials and turns them into per-request options.

    The credentials are client configuration (the ``webhook_secret`` precedent), so
    the check for them happens while building the request options — before the call
    reaches the transport — and a missing credential is a ``BirdError``, not a 401.
    """

    def __init__(self, key: str | None, secret: str | None) -> None:
        self._key = key
        self._secret = secret

    def options(
        self, options: RequestOptions | None, query: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        if not self._key or not self._secret:
            raise BirdError(
                "missing Realtime app credentials: pass realtime_key= and realtime_secret= "
                "when constructing the client. They are the Realtime app's own key and "
                "secret, not your Bird API key."
            )
        kwargs: dict[str, Any] = dict(options or {})
        # The credentials win over a caller's extra_headers — they authenticate the app,
        # not a per-call detail. Query params merge the same way the stats reads do.
        kwargs["extra_headers"] = {
            **(kwargs.get("extra_headers") or {}),
            "X-Realtime-Key": self._key,
            "X-Realtime-Secret": self._secret,
        }
        if query:
            kwargs["extra_query"] = {**(kwargs.get("extra_query") or {}), **query}
        return kwargs


def _channels_query(prefix: str | None, include: Sequence[str] | None) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if prefix is not None:
        query["prefix"] = prefix
    if include:
        query["include"] = list(include)
    return query


class RealtimeChannels:
    """Live channel state reads. Reach it via ``client.realtime.channels``."""

    def __init__(self, client: SyncAPIClient, auth: _RealtimeAuth) -> None:
        self._client = client
        self._auth = auth

    def list(
        self,
        realtime_app_id: str,
        *,
        prefix: str | None = None,
        include: Sequence[str] | None = None,
        options: RequestOptions | None = None,
    ) -> RealtimeChannelsList:
        """List the app's currently occupied channels, sorted by name. This is a
        point-in-time snapshot of live state, not a paginated collection — the full
        set comes back in one response; narrow it with ``prefix``.

        ``include`` asks for per-channel counts: ``member_count`` needs a
        presence-channel ``prefix`` and ``connection_count`` needs the app's
        connection-counting flag, otherwise the API returns a validation error.

        ```python
        channels = client.realtime.channels.list("rap_01krd...", prefix="presence-")
        for channel in channels.data:
            print(channel.name)
        ```
        """
        response = self._client.request(
            "GET",
            _app_path(realtime_app_id, "channels"),
            **self._auth.options(options, _channels_query(prefix, include)),
        )
        return RealtimeChannelsList.model_validate(response.json())

    def get(
        self,
        realtime_app_id: str,
        channel_name: str,
        *,
        include: Sequence[str] | None = None,
        options: RequestOptions | None = None,
    ) -> RealtimeChannelInfo:
        """Read one channel's live state. An unoccupied channel is not an error —
        it comes back with ``occupied=False``.

        ```python
        channel = client.realtime.channels.get(
            "rap_01krd...", "presence-lobby", include=["member_count"]
        )
        print(channel.occupied, channel.member_count)
        ```
        """
        response = self._client.request(
            "GET",
            _app_path(realtime_app_id, "channels", channel_name),
            **self._auth.options(options, _channels_query(None, include)),
        )
        return RealtimeChannelInfo.model_validate(response.json())

    def members(
        self,
        realtime_app_id: str,
        channel_name: str,
        *,
        options: RequestOptions | None = None,
    ) -> RealtimeChannelMembers:
        """List the members currently present on a presence channel. Only
        ``presence-`` channels carry membership; asking about any other channel is a
        validation error.

        ```python
        members = client.realtime.channels.members("rap_01krd...", "presence-lobby")
        print([member.member_id for member in members.members])
        ```
        """
        response = self._client.request(
            "GET",
            _app_path(realtime_app_id, "channels", channel_name, "members"),
            **self._auth.options(options),
        )
        return RealtimeChannelMembers.model_validate(response.json())


class RealtimeMembers:
    """Presence member operations. Reach it via ``client.realtime.members``."""

    def __init__(self, client: SyncAPIClient, auth: _RealtimeAuth) -> None:
        self._client = client
        self._auth = auth

    def send(
        self,
        realtime_app_id: str,
        member_id: str,
        *,
        event: str,
        data: Any = None,
        options: RequestOptions | None = None,
    ) -> None:
        """Send an event to one member instead of to a channel. Every connection that
        member currently holds receives it, across tabs and devices, so there is no
        need to track their connections or give them a channel of their own. The
        member must have signed in on the connection to be addressable.

        Delivery is best-effort: a member holding no connections right now simply does
        not receive the event, and that is not reported back.

        ```python
        client.realtime.members.send(
            "rap_01krd...", "member:42", event="order-shipped", data={"id": 42}
        )
        ```
        """
        self._client.request(
            "POST",
            _app_path(realtime_app_id, "members", member_id, "events"),
            body=_member_send_body(event=event, data=data),
            **self._auth.options(options),
        )

    def disconnect(
        self,
        realtime_app_id: str,
        member_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Disconnect a member — every connection that authenticated as this member
        id is closed. Clients reconnect on their own unless your auth server stops
        authorizing them, so pair this with revoking the member's access.

        ```python
        client.realtime.members.disconnect("rap_01krd...", "member:42")
        ```
        """
        self._client.request(
            "POST",
            _app_path(realtime_app_id, "members", member_id, "disconnect"),
            **self._auth.options(options),
        )


class Realtime:
    """The Realtime channel namespace. Reach it via ``client.realtime``."""

    def __init__(self, client: SyncAPIClient, key: str | None, secret: str | None) -> None:
        self._client = client
        self._auth = _RealtimeAuth(key, secret)
        self.channels = RealtimeChannels(client, self._auth)
        self.members = RealtimeMembers(client, self._auth)

    def publish(
        self,
        realtime_app_id: str,
        *,
        event: str,
        channels: Sequence[str],
        data: Any = None,
        exclude_connection_id: str | None = None,
        include: Sequence[str] | None = None,
        options: RequestOptions | None = None,
    ) -> RealtimePublishResult:
        """Publish one event to up to 100 channels. ``data`` is any JSON value (10 KB
        serialized), and ``exclude_connection_id`` skips the connection that triggered
        the change so a client doesn't receive an echo of its own action.

        ```python
        client.realtime.publish(
            "rap_01krd...",
            event="order-updated",
            channels=["orders", "orders-42"],
            data={"id": 42, "status": "shipped"},
        )
        ```
        """
        body = _publish_body(
            event=event,
            channels=channels,
            data=data,
            exclude_connection_id=exclude_connection_id,
            include=include,
        )
        response = self._client.request(
            "POST", _app_path(realtime_app_id, "events"), body=body, **self._auth.options(options)
        )
        return RealtimePublishResult.model_validate(response.json())

    def publish_batch(
        self,
        realtime_app_id: str,
        *,
        events: Sequence[RealtimeBatchEventParams],
        options: RequestOptions | None = None,
    ) -> RealtimeBatchPublishResult:
        """Publish up to 10 events in one call. Unlike ``publish``, each batch event
        targets a single ``channel``. The whole batch is validated before any event is
        delivered, and the result is positional — one entry per event, in request order.

        ```python
        client.realtime.publish_batch(
            "rap_01krd...",
            events=[
                {"event": "order-created", "channel": "orders", "data": {"id": 1}},
                {"event": "order-updated", "channel": "orders", "data": {"id": 2}},
            ],
        )
        ```
        """
        response = self._client.request(
            "POST",
            _app_path(realtime_app_id, "batch-events"),
            body=_batch_body(events),
            **self._auth.options(options),
        )
        return RealtimeBatchPublishResult.model_validate(response.json())


class AsyncRealtimeChannels:
    """Async mirror of `RealtimeChannels`."""

    def __init__(self, client: AsyncAPIClient, auth: _RealtimeAuth) -> None:
        self._client = client
        self._auth = auth

    async def list(
        self,
        realtime_app_id: str,
        *,
        prefix: str | None = None,
        include: Sequence[str] | None = None,
        options: RequestOptions | None = None,
    ) -> RealtimeChannelsList:
        """List the app's currently occupied channels (async)."""
        response = await self._client.request(
            "GET",
            _app_path(realtime_app_id, "channels"),
            **self._auth.options(options, _channels_query(prefix, include)),
        )
        return RealtimeChannelsList.model_validate(response.json())

    async def get(
        self,
        realtime_app_id: str,
        channel_name: str,
        *,
        include: Sequence[str] | None = None,
        options: RequestOptions | None = None,
    ) -> RealtimeChannelInfo:
        """Read one channel's live state (async)."""
        response = await self._client.request(
            "GET",
            _app_path(realtime_app_id, "channels", channel_name),
            **self._auth.options(options, _channels_query(None, include)),
        )
        return RealtimeChannelInfo.model_validate(response.json())

    async def members(
        self,
        realtime_app_id: str,
        channel_name: str,
        *,
        options: RequestOptions | None = None,
    ) -> RealtimeChannelMembers:
        """List the members present on a presence channel (async)."""
        response = await self._client.request(
            "GET",
            _app_path(realtime_app_id, "channels", channel_name, "members"),
            **self._auth.options(options),
        )
        return RealtimeChannelMembers.model_validate(response.json())


class AsyncRealtimeMembers:
    """Async mirror of `RealtimeMembers`."""

    def __init__(self, client: AsyncAPIClient, auth: _RealtimeAuth) -> None:
        self._client = client
        self._auth = auth

    async def send(
        self,
        realtime_app_id: str,
        member_id: str,
        *,
        event: str,
        data: Any = None,
        options: RequestOptions | None = None,
    ) -> None:
        """Send an event to every connection this member holds (async)."""
        await self._client.request(
            "POST",
            _app_path(realtime_app_id, "members", member_id, "events"),
            body=_member_send_body(event=event, data=data),
            **self._auth.options(options),
        )

    async def disconnect(
        self,
        realtime_app_id: str,
        member_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> None:
        """Disconnect every connection authenticated as this member id (async)."""
        await self._client.request(
            "POST",
            _app_path(realtime_app_id, "members", member_id, "disconnect"),
            **self._auth.options(options),
        )


class AsyncRealtime:
    """Async Realtime namespace. Reach it via ``client.realtime``."""

    def __init__(self, client: AsyncAPIClient, key: str | None, secret: str | None) -> None:
        self._client = client
        self._auth = _RealtimeAuth(key, secret)
        self.channels = AsyncRealtimeChannels(client, self._auth)
        self.members = AsyncRealtimeMembers(client, self._auth)

    async def publish(
        self,
        realtime_app_id: str,
        *,
        event: str,
        channels: Sequence[str],
        data: Any = None,
        exclude_connection_id: str | None = None,
        include: Sequence[str] | None = None,
        options: RequestOptions | None = None,
    ) -> RealtimePublishResult:
        """Publish one event to up to 100 channels (async)."""
        body = _publish_body(
            event=event,
            channels=channels,
            data=data,
            exclude_connection_id=exclude_connection_id,
            include=include,
        )
        response = await self._client.request(
            "POST", _app_path(realtime_app_id, "events"), body=body, **self._auth.options(options)
        )
        return RealtimePublishResult.model_validate(response.json())

    async def publish_batch(
        self,
        realtime_app_id: str,
        *,
        events: Sequence[RealtimeBatchEventParams],
        options: RequestOptions | None = None,
    ) -> RealtimeBatchPublishResult:
        """Publish up to 10 events in one call (async)."""
        response = await self._client.request(
            "POST",
            _app_path(realtime_app_id, "batch-events"),
            body=_batch_body(events),
            **self._auth.options(options),
        )
        return RealtimeBatchPublishResult.model_validate(response.json())
