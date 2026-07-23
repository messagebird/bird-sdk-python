"""The email statistics reads: ``client.email.stats.<method>``.

A read-only namespace nested under the email channel. Every method is a ``GET``
that returns a typed aggregate for the requested period; all query parameters are
optional, and the server applies its own window defaults when they are omitted.
The dimension filters (``category``/``sending_domain``/``tag``/``sending_ip``/
``recipient_domain``/``template``) are mutually exclusive — set at most one.
"""

from __future__ import annotations

from typing import Any, TypeVar

import pydantic

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import (
    EmailStatsByBounceCodeResponse,
    EmailStatsByBroadcastResponse,
    EmailStatsByCategoryResponse,
    EmailStatsByClientResponse,
    EmailStatsByComplaintTypeResponse,
    EmailStatsByLocationResponse,
    EmailStatsByMailboxProviderRegionResponse,
    EmailStatsByMailboxProviderResponse,
    EmailStatsByRecipientDomainResponse,
    EmailStatsBySendingDomainResponse,
    EmailStatsBySendingIpResponse,
    EmailStatsByTemplateResponse,
    EmailStatsResponse,
    EmailStatsSummary,
    EmailStatsTagsResponse,
)
from bird._types import RequestOptions

_BASE = "/v1/email/stats"

T = TypeVar("T", bound=pydantic.BaseModel)


def _stats_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _request_kwargs(options: RequestOptions | None, query: dict[str, object]) -> dict[str, Any]:
    # Stats are plain GETs, so the built query rides in as extra_query, merged over
    # any extra_query the caller passed via options (the same threading pagination does).
    kwargs: dict[str, Any] = dict(options or {})
    kwargs["extra_query"] = {**(kwargs.get("extra_query") or {}), **query}
    return kwargs


class EmailStats:
    """Aggregate email statistics reads. Reach it via ``client.email.stats``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def _get(self, path: str, query: dict[str, object], model: type[T], options: RequestOptions | None) -> T:
        response = self._client.request("GET", f"{_BASE}/{path}", **_request_kwargs(options, query))
        return model.model_validate(response.json())

    def summary(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sending_domain: str | None = None,
        tag: str | None = None,
        sending_ip: str | None = None,
        recipient_domain: str | None = None,
        template: str | None = None,
        compare: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsSummary:
        """Return a single-row aggregate (delivery, bounce, complaint, open, click,
        and latency percentiles) across the requested period.

        ```python
        summary = client.email.stats.summary(from_="2026-05-01", to="2026-05-25")
        print(summary.sends_accepted, summary.delivery)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sending_domain": sending_domain, "tag": tag, "sending_ip": sending_ip,
            "recipient_domain": recipient_domain, "template": template, "compare": compare,
        })
        return self._get("summary", query, EmailStatsSummary, options)

    def daily(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sending_domain: str | None = None,
        tag: str | None = None,
        sending_ip: str | None = None,
        recipient_domain: str | None = None,
        template: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsResponse:
        """Return one aggregate row per calendar day for the requested period.

        ```python
        stats = client.email.stats.daily(from_="2026-05-01", to="2026-05-25")
        for point in stats.data:
            print(point.bucket, point.sends_accepted)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sending_domain": sending_domain, "tag": tag, "sending_ip": sending_ip,
            "recipient_domain": recipient_domain, "template": template,
        })
        return self._get("daily", query, EmailStatsResponse, options)

    def hourly(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sending_domain: str | None = None,
        tag: str | None = None,
        sending_ip: str | None = None,
        recipient_domain: str | None = None,
        template: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsResponse:
        """Return one aggregate row per hour for the requested period (max 30 days).

        ```python
        stats = client.email.stats.hourly(
            from_="2026-05-25T00:00:00Z",
            to="2026-05-25T23:59:59Z",
        )
        for point in stats.data:
            print(point.bucket, point.delivery)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sending_domain": sending_domain, "tag": tag, "sending_ip": sending_ip,
            "recipient_domain": recipient_domain, "template": template,
        })
        return self._get("hourly", query, EmailStatsResponse, options)

    def by_tag(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsTagsResponse:
        """Return delivery and engagement counts grouped by tag, ranked by ``sort``.

        ```python
        stats = client.email.stats.by_tag(from_="2026-05-01", to="2026-05-25", sort="delivered")
        for row in stats.data:
            print(row)
        print(stats.total)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("tags", query, EmailStatsTagsResponse, options)

    def by_category(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByCategoryResponse:
        """Return counts grouped by category (``transactional`` / ``marketing``).

        ```python
        stats = client.email.stats.by_category(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("categories", query, EmailStatsByCategoryResponse, options)

    def by_sending_ip(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsBySendingIpResponse:
        """Return delivery and deliverability counts grouped by sending IP.

        ```python
        stats = client.email.stats.by_sending_ip(
            from_="2026-05-01", to="2026-05-25", sort="bounces.block",
        )
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("sending-ips", query, EmailStatsBySendingIpResponse, options)

    def by_sending_domain(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsBySendingDomainResponse:
        """Return counts grouped by sending domain.

        ```python
        stats = client.email.stats.by_sending_domain(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("sending-domains", query, EmailStatsBySendingDomainResponse, options)

    def by_recipient_domain(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByRecipientDomainResponse:
        """Return counts grouped by recipient mailbox domain (e.g. ``gmail.com``).

        ```python
        stats = client.email.stats.by_recipient_domain(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("recipient-domains", query, EmailStatsByRecipientDomainResponse, options)

    def by_mailbox_provider(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByMailboxProviderResponse:
        """Return counts grouped by mailbox provider.

        ```python
        stats = client.email.stats.by_mailbox_provider(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("mailbox-providers", query, EmailStatsByMailboxProviderResponse, options)

    def by_mailbox_provider_region(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByMailboxProviderRegionResponse:
        """Return counts grouped by mailbox provider region.

        ```python
        stats = client.email.stats.by_mailbox_provider_region(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("mailbox-provider-regions", query, EmailStatsByMailboxProviderRegionResponse, options)

    def by_template(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByTemplateResponse:
        """Return counts grouped by template.

        ```python
        stats = client.email.stats.by_template(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("templates", query, EmailStatsByTemplateResponse, options)

    def by_location(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        group_by: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByLocationResponse:
        """Return engagement counts grouped by recipient location.

        Set ``group_by`` to ``country`` (default), ``region``, or ``city``.

        ```python
        stats = client.email.stats.by_location(
            from_="2026-05-01", to="2026-05-25", group_by="country",
        )
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "group_by": group_by, "sort": sort, "limit": limit,
        })
        return self._get("locations", query, EmailStatsByLocationResponse, options)

    def by_client(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        group_by: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByClientResponse:
        """Return engagement counts grouped by email client.

        Set ``group_by`` to ``email_client`` (default), ``os``, or ``device_type``.

        ```python
        stats = client.email.stats.by_client(
            from_="2026-05-01", to="2026-05-25", group_by="email_client",
        )
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "group_by": group_by, "sort": sort, "limit": limit,
        })
        return self._get("clients", query, EmailStatsByClientResponse, options)

    def by_bounce_code(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByBounceCodeResponse:
        """Return bounce counts grouped by bounce code.

        ```python
        stats = client.email.stats.by_bounce_code(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit,
        })
        return self._get("bounce-codes", query, EmailStatsByBounceCodeResponse, options)

    def by_complaint_type(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByComplaintTypeResponse:
        """Return complaint counts grouped by complaint type.

        ```python
        stats = client.email.stats.by_complaint_type(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit,
        })
        return self._get("complaint-types", query, EmailStatsByComplaintTypeResponse, options)

    def by_broadcast(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByBroadcastResponse:
        """Return counts grouped by broadcast.

        ```python
        stats = client.email.stats.by_broadcast(from_="2026-05-01", to="2026-05-25")
        for row in stats.data:
            print(row)
        ```
        """
        query = _stats_query({
            "from": from_, "to": to, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return self._get("broadcasts", query, EmailStatsByBroadcastResponse, options)


class AsyncEmailStats:
    """Async mirror of `EmailStats`: ``await`` each read. Reach it via ``client.email.stats``."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def _get(self, path: str, query: dict[str, object], model: type[T], options: RequestOptions | None) -> T:
        response = await self._client.request("GET", f"{_BASE}/{path}", **_request_kwargs(options, query))
        return model.model_validate(response.json())

    async def summary(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sending_domain: str | None = None,
        tag: str | None = None,
        sending_ip: str | None = None,
        recipient_domain: str | None = None,
        template: str | None = None,
        compare: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsSummary:
        """Return a single-row aggregate across the requested period (see `EmailStats.summary`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sending_domain": sending_domain, "tag": tag, "sending_ip": sending_ip,
            "recipient_domain": recipient_domain, "template": template, "compare": compare,
        })
        return await self._get("summary", query, EmailStatsSummary, options)

    async def daily(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sending_domain: str | None = None,
        tag: str | None = None,
        sending_ip: str | None = None,
        recipient_domain: str | None = None,
        template: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsResponse:
        """Return one aggregate row per calendar day (see `EmailStats.daily`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sending_domain": sending_domain, "tag": tag, "sending_ip": sending_ip,
            "recipient_domain": recipient_domain, "template": template,
        })
        return await self._get("daily", query, EmailStatsResponse, options)

    async def hourly(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sending_domain: str | None = None,
        tag: str | None = None,
        sending_ip: str | None = None,
        recipient_domain: str | None = None,
        template: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsResponse:
        """Return one aggregate row per hour (see `EmailStats.hourly`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sending_domain": sending_domain, "tag": tag, "sending_ip": sending_ip,
            "recipient_domain": recipient_domain, "template": template,
        })
        return await self._get("hourly", query, EmailStatsResponse, options)

    async def by_tag(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsTagsResponse:
        """Return counts grouped by tag (see `EmailStats.byTag`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("tags", query, EmailStatsTagsResponse, options)

    async def by_category(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByCategoryResponse:
        """Return counts grouped by category (see `EmailStats.byCategory`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("categories", query, EmailStatsByCategoryResponse, options)

    async def by_sending_ip(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsBySendingIpResponse:
        """Return counts grouped by sending IP (see `EmailStats.bySendingIp`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("sending-ips", query, EmailStatsBySendingIpResponse, options)

    async def by_sending_domain(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsBySendingDomainResponse:
        """Return counts grouped by sending domain (see `EmailStats.bySendingDomain`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("sending-domains", query, EmailStatsBySendingDomainResponse, options)

    async def by_recipient_domain(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByRecipientDomainResponse:
        """Return counts grouped by recipient mailbox domain (see `EmailStats.byRecipientDomain`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("recipient-domains", query, EmailStatsByRecipientDomainResponse, options)

    async def by_mailbox_provider(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByMailboxProviderResponse:
        """Return counts grouped by mailbox provider (see `EmailStats.byMailboxProvider`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("mailbox-providers", query, EmailStatsByMailboxProviderResponse, options)

    async def by_mailbox_provider_region(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByMailboxProviderRegionResponse:
        """Return counts grouped by mailbox provider region (see `EmailStats.byMailboxProviderRegion`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("mailbox-provider-regions", query, EmailStatsByMailboxProviderRegionResponse, options)

    async def by_template(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByTemplateResponse:
        """Return counts grouped by template (see `EmailStats.byTemplate`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("templates", query, EmailStatsByTemplateResponse, options)

    async def by_location(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        group_by: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByLocationResponse:
        """Return counts grouped by recipient location (see `EmailStats.byLocation`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "group_by": group_by, "sort": sort, "limit": limit,
        })
        return await self._get("locations", query, EmailStatsByLocationResponse, options)

    async def by_client(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        group_by: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByClientResponse:
        """Return counts grouped by email client (see `EmailStats.byClient`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "group_by": group_by, "sort": sort, "limit": limit,
        })
        return await self._get("clients", query, EmailStatsByClientResponse, options)

    async def by_bounce_code(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByBounceCodeResponse:
        """Return bounce counts grouped by bounce code (see `EmailStats.byBounceCode`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit,
        })
        return await self._get("bounce-codes", query, EmailStatsByBounceCodeResponse, options)

    async def by_complaint_type(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        timezone: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByComplaintTypeResponse:
        """Return complaint counts grouped by complaint type (see `EmailStats.byComplaintType`)."""
        query = _stats_query({
            "from": from_, "to": to, "timezone": timezone, "category": category,
            "sort": sort, "limit": limit,
        })
        return await self._get("complaint-types", query, EmailStatsByComplaintTypeResponse, options)

    async def by_broadcast(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        category: str | None = None,
        sort: str | None = None,
        limit: int | None = None,
        include_trend: bool | None = None,
        trend_grain: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailStatsByBroadcastResponse:
        """Return counts grouped by broadcast (see `EmailStats.byBroadcast`)."""
        query = _stats_query({
            "from": from_, "to": to, "category": category,
            "sort": sort, "limit": limit, "include_trend": include_trend, "trend_grain": trend_grain,
        })
        return await self._get("broadcasts", query, EmailStatsByBroadcastResponse, options)
