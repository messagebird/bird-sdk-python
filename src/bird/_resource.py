"""Shared base for the generated resource facades.

A generated ``<Res>`` subclasses :class:`Resource` (sync) and ``Async<Res>``
subclasses :class:`AsyncResource`; the client handle and the request-core
helpers live here once instead of being emitted into every resource file
(the Go/TS SDKs share a resource base the same way).
"""

from __future__ import annotations

from typing import Any, TypeVar

import pydantic

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._types import RequestOptions

T = TypeVar("T", bound=pydantic.BaseModel)


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    """Per-call options as request kwargs — a plain ``dict[str, Any]`` to spread
    into ``request()``; a bare ``dict(options)`` widens the values to ``object``."""
    return dict(options or {})


def _request_kwargs(
    options: RequestOptions | None, query: dict[str, object]
) -> dict[str, Any]:
    """Merge the built query into ``extra_query`` (dropping None-valued params),
    over any ``extra_query`` the caller passed via ``options``."""
    clean = {key: value for key, value in query.items() if value is not None}
    kwargs = _opts(options)
    kwargs["extra_query"] = {**(kwargs.get("extra_query") or {}), **clean}
    return kwargs


class Resource:
    """Sync request core; reached through a generated ``<Res>`` subclass."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def _get(
        self,
        path: str,
        query: dict[str, object],
        model: type[T],
        options: RequestOptions | None,
    ) -> T:
        response = self._client.request("GET", path, **_request_kwargs(options, query))
        return model.model_validate(response.json())

    def _write(
        self,
        verb: str,
        path: str,
        body: dict[str, object],
        model: type[T],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> T:
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        response = self._client.request(verb, path, body=body, **kwargs)
        return model.model_validate(response.json())

    def _write_none(
        self,
        verb: str,
        path: str,
        body: dict[str, object],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> None:
        """A write whose success is 204 (no body): same write lifecycle as
        :meth:`_write`, but the response is discarded."""
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        self._client.request(verb, path, body=body, **kwargs)

    def _action(
        self,
        verb: str,
        path: str,
        model: type[T],
        options: RequestOptions | None,
    ) -> T:
        response = self._client.request(verb, path, **_opts(options))
        return model.model_validate(response.json())

    def _action_none(self, verb: str, path: str, options: RequestOptions | None) -> None:
        self._client.request(verb, path, **_opts(options))

    def _delete(
        self,
        path: str,
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> None:
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        self._client.request("DELETE", path, **kwargs)


class AsyncResource:
    """Async mirror of :class:`Resource`."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def _get(
        self,
        path: str,
        query: dict[str, object],
        model: type[T],
        options: RequestOptions | None,
    ) -> T:
        response = await self._client.request(
            "GET", path, **_request_kwargs(options, query)
        )
        return model.model_validate(response.json())

    async def _write(
        self,
        verb: str,
        path: str,
        body: dict[str, object],
        model: type[T],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> T:
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        response = await self._client.request(verb, path, body=body, **kwargs)
        return model.model_validate(response.json())

    async def _write_none(
        self,
        verb: str,
        path: str,
        body: dict[str, object],
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> None:
        """A write whose success is 204 (no body): same write lifecycle as
        :meth:`_write`, but the response is discarded."""
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        await self._client.request(verb, path, body=body, **kwargs)

    async def _action(
        self,
        verb: str,
        path: str,
        model: type[T],
        options: RequestOptions | None,
    ) -> T:
        response = await self._client.request(verb, path, **_opts(options))
        return model.model_validate(response.json())

    async def _action_none(self, verb: str, path: str, options: RequestOptions | None) -> None:
        await self._client.request(verb, path, **_opts(options))

    async def _delete(
        self,
        path: str,
        options: RequestOptions | None,
        query: dict[str, object] | None = None,
    ) -> None:
        kwargs = _request_kwargs(options, query) if query else _opts(options)
        await self._client.request("DELETE", path, **kwargs)
