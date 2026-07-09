"""Workspace email templates: ``client.email_templates`` — create/list/get/update/
delete/publish a template, and read its versions.

A template owns an editable draft; :meth:`EmailTemplates.publish` snapshots the draft
into an immutable numbered version and makes it the live version that sends use. Send
by a published template with ``client.email.send(template="emt_abc123")``.
"""

from __future__ import annotations

from typing import Any

from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird._generated import (
    EmailTemplate,
    EmailTemplateCreate,
    EmailTemplateSummary,
    EmailTemplateUpdate,
    EmailTemplateVersion,
    EmailTemplateVersionList,
)
from bird._models import to_wire
from bird._types import RequestOptions
from bird.pagination import AsyncPage, SyncPage

_PATH = "/v1/email/templates"


def _opts(options: RequestOptions | None) -> dict[str, Any]:
    return dict(options or {})


def _list_query(values: dict[str, Any]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _create_body(
    *,
    name: str,
    category: str,
    source: str,
    description: str | None,
    subject: str | None,
    html: str | None,
    text: str | None,
    brand_kit_id: str | None,
) -> dict[str, Any]:
    return to_wire(EmailTemplateCreate, {
        "name":         name,
        "category":     category,
        "source":       source,
        "description":  description,
        "subject":      subject,
        "html":         html,
        "text":         text,
        "brand_kit_id": brand_kit_id,
    })


def _update_body(
    *,
    revision: int,
    name: str | None,
    description: str | None,
    subject: str | None,
    html: str | None,
    text: str | None,
    brand_kit_id: str | None,
) -> dict[str, Any]:
    # `revision` is required (optimistic-lock check); every other field is omitted
    # when left unset, leaving it unchanged.
    return to_wire(EmailTemplateUpdate, {
        "revision":     revision,
        "name":         name,
        "description":  description,
        "subject":      subject,
        "html":         html,
        "text":         text,
        "brand_kit_id": brand_kit_id,
    })


class EmailTemplates:
    """Manage workspace email templates. Reach it via ``client.email_templates``."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def create(
        self,
        *,
        name: str,
        category: str,
        source: str,
        description: str | None = None,
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        brand_kit_id: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailTemplate:
        """Create a template and its initial editable draft.

        ``source`` is the authoring format (``handlebars``, ``liquid``, or ``html``),
        fixed at creation; ``liquid`` currently supports variable substitution only.

        ```python
        tpl = client.email_templates.create(
            name="welcome-email",
            description="Welcome",
            category="transactional",
            source="handlebars",
            subject="Welcome, {{ first_name }}!",
            html="<h1>Hi {{ first_name }}</h1>",
        )
        print(tpl.id, tpl.revision)
        ```
        """
        body = _create_body(
            name=name, category=category, source=source, description=description,
            subject=subject, html=html, text=text, brand_kit_id=brand_kit_id,
        )
        response = self._client.request("POST", _PATH, body=body, **_opts(options))
        return EmailTemplate.model_validate(response.json())

    def get(self, template_id: str, *, options: RequestOptions | None = None) -> EmailTemplate:
        """Fetch a template with its current draft content."""
        response = self._client.request("GET", f"{_PATH}/{template_id}", **_opts(options))
        return EmailTemplate.model_validate(response.json())

    def update(
        self,
        template_id: str,
        *,
        revision: int,
        name: str | None = None,
        description: str | None = None,
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        brand_kit_id: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailTemplate:
        """Edit a template's metadata and draft content. Only the fields you pass
        change. ``revision`` is the draft revision you last read — a stale value
        returns a conflict, so concurrent edits are detected.
        """
        body = _update_body(
            revision=revision, name=name, description=description, subject=subject,
            html=html, text=text, brand_kit_id=brand_kit_id,
        )
        response = self._client.request("PATCH", f"{_PATH}/{template_id}", body=body, **_opts(options))
        return EmailTemplate.model_validate(response.json())

    def delete(self, template_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete a template and all its versions. Its name becomes available for reuse."""
        self._client.request("DELETE", f"{_PATH}/{template_id}", **_opts(options))

    def publish(self, template_id: str, *, options: RequestOptions | None = None) -> EmailTemplateVersion:
        """Publish the current draft as a new immutable, numbered version and make it
        the live version used by sends. The draft stays editable.

        ```python
        version = client.email_templates.publish("emt_abc123")
        print(version.version_number)

        client.email.send(
            from_="hello@acme.com",
            to=["alice@example.com"],
            template="emt_abc123",
            parameters={"first_name": "Alice"},
        )
        ```
        """
        response = self._client.request("POST", f"{_PATH}/{template_id}/publish", **_opts(options))
        return EmailTemplateVersion.model_validate(response.json())

    def list_versions(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> EmailTemplateVersionList:
        """Return every version of a template — the current draft plus all published
        versions — newest first, in ``.data``. Not paginated."""
        response = self._client.request("GET", f"{_PATH}/{template_id}/versions", **_opts(options))
        return EmailTemplateVersionList.model_validate(response.json())

    def get_version(
        self, template_id: str, version_id: str, *, options: RequestOptions | None = None
    ) -> EmailTemplateVersion:
        """Return a single version of a template."""
        response = self._client.request(
            "GET", f"{_PATH}/{template_id}/versions/{version_id}", **_opts(options)
        )
        return EmailTemplateVersion.model_validate(response.json())

    def list(
        self,
        *,
        category: str | None = None,
        source: str | None = None,
        name: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[EmailTemplateSummary]:
        """List templates, newest first; iterate the page to auto-paginate.

        ```python
        for template in client.email_templates.list(category="transactional"):
            print(template.id, template.name)
        ```
        """
        query = _list_query({
            "category": category, "source": source, "name": name,
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return SyncPage(self._client, _PATH, query, EmailTemplateSummary, options)


class AsyncEmailTemplates:
    """Async mirror of `EmailTemplates`: ``await`` each call, ``async for`` over a list."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        name: str,
        category: str,
        source: str,
        description: str | None = None,
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        brand_kit_id: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailTemplate:
        """Create a template and its initial editable draft."""
        body = _create_body(
            name=name, category=category, source=source, description=description,
            subject=subject, html=html, text=text, brand_kit_id=brand_kit_id,
        )
        response = await self._client.request("POST", _PATH, body=body, **_opts(options))
        return EmailTemplate.model_validate(response.json())

    async def get(self, template_id: str, *, options: RequestOptions | None = None) -> EmailTemplate:
        """Fetch a template with its current draft content."""
        response = await self._client.request("GET", f"{_PATH}/{template_id}", **_opts(options))
        return EmailTemplate.model_validate(response.json())

    async def update(
        self,
        template_id: str,
        *,
        revision: int,
        name: str | None = None,
        description: str | None = None,
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        brand_kit_id: str | None = None,
        options: RequestOptions | None = None,
    ) -> EmailTemplate:
        """Edit a template's metadata and draft content. Only the fields you pass
        change. ``revision`` is the draft revision you last read."""
        body = _update_body(
            revision=revision, name=name, description=description, subject=subject,
            html=html, text=text, brand_kit_id=brand_kit_id,
        )
        response = await self._client.request(
            "PATCH", f"{_PATH}/{template_id}", body=body, **_opts(options)
        )
        return EmailTemplate.model_validate(response.json())

    async def delete(self, template_id: str, *, options: RequestOptions | None = None) -> None:
        """Delete a template and all its versions. Its name becomes available for reuse."""
        await self._client.request("DELETE", f"{_PATH}/{template_id}", **_opts(options))

    async def publish(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> EmailTemplateVersion:
        """Publish the current draft as a new immutable, numbered version and make it
        the live version used by sends. The draft stays editable."""
        response = await self._client.request(
            "POST", f"{_PATH}/{template_id}/publish", **_opts(options)
        )
        return EmailTemplateVersion.model_validate(response.json())

    async def list_versions(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> EmailTemplateVersionList:
        """Return every version of a template — the current draft plus all published
        versions — newest first, in ``.data``. Not paginated."""
        response = await self._client.request(
            "GET", f"{_PATH}/{template_id}/versions", **_opts(options)
        )
        return EmailTemplateVersionList.model_validate(response.json())

    async def get_version(
        self, template_id: str, version_id: str, *, options: RequestOptions | None = None
    ) -> EmailTemplateVersion:
        """Return a single version of a template."""
        response = await self._client.request(
            "GET", f"{_PATH}/{template_id}/versions/{version_id}", **_opts(options)
        )
        return EmailTemplateVersion.model_validate(response.json())

    def list(
        self,
        *,
        category: str | None = None,
        source: str | None = None,
        name: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[EmailTemplateSummary]:
        """List templates, newest first; ``async for`` over the page to auto-paginate."""
        query = _list_query({
            "category": category, "source": source, "name": name,
            "limit": limit, "starting_after": starting_after, "ending_before": ending_before,
        })
        return AsyncPage(self._client, _PATH, query, EmailTemplateSummary, options)
