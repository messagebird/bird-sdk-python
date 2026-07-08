"""Workspace SMS templates: ``client.sms_templates`` — list the templates
available to the workspace and read one back by its alias or id.

The catalogue holds Bird's built-in templates plus any the workspace authored,
and is read-only through this SDK.
"""

from __future__ import annotations

from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import SMSTemplate, SMSTemplateList
from bird._types import RequestOptions

_PATH = "/v1/sms/templates"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_opts(
    options: RequestOptions | None,
    scope: str | None,
    category: str | None,
    locale: str | None,
) -> dict[str, Any]:
    # Fold the filters into extra_query; a caller-supplied extra_query wins on a clash.
    query = {key: value for key, value in {"scope": scope, "category": category, "locale": locale}.items() if value is not None}
    opts = _opts(options)
    if query:
        opts["extra_query"] = {**query, **opts.get("extra_query", {})}
    return opts


class SMSTemplates:
    """Read workspace SMS templates. Reach it via ``client.sms_templates``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def list(
        self,
        *,
        scope: str | None = None,
        category: str | None = None,
        locale: str | None = None,
        options: RequestOptions | None = None,
    ) -> SMSTemplateList:
        """List the SMS templates available to the workspace — Bird's built-in
        templates plus any the workspace authored. The catalogue is small and
        returned in full in ``.data``; this list is not paginated. Filter by
        ``scope``, ``category``, or ``locale`` (a BCP-47 language tag).

        ```python
        templates = client.sms_templates.list(scope="system")
        for template in templates.data:
            print(template.id, template.name)
        ```
        """
        response = self._client.request("GET", _PATH, **_list_opts(options, scope, category, locale))
        return SMSTemplateList.model_validate(response.json())

    def get(self, template_ref: str, *, options: RequestOptions | None = None) -> SMSTemplate:
        """Fetch a single SMS template by its alias or id, including its body and
        the variables it expects.

        ```python
        template = client.sms_templates.get("bird_otp_verification")
        print(template.body, template.variables)
        ```
        """
        response = self._client.request("GET", f"{_PATH}/{template_ref}", **_opts(options))
        return SMSTemplate.model_validate(response.json())


class AsyncSMSTemplates:
    """Async mirror of `SMSTemplates`: ``await`` each call."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        scope: str | None = None,
        category: str | None = None,
        locale: str | None = None,
        options: RequestOptions | None = None,
    ) -> SMSTemplateList:
        """List the SMS templates available to the workspace. Not paginated —
        the full catalogue is returned in ``.data``. Filter by ``scope``,
        ``category``, or ``locale``."""
        response = await self._client.request("GET", _PATH, **_list_opts(options, scope, category, locale))
        return SMSTemplateList.model_validate(response.json())

    async def get(self, template_ref: str, *, options: RequestOptions | None = None) -> SMSTemplate:
        """Fetch a single SMS template by its alias or id."""
        response = await self._client.request("GET", f"{_PATH}/{template_ref}", **_opts(options))
        return SMSTemplate.model_validate(response.json())
