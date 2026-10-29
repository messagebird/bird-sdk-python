from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from bird._generated import AMBMessage, AMBMessageSendRequest
from bird._models import to_wire
from bird._types import RequestOptions
from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.amb_gen import AsyncAmbBase, AmbBase
from bird.resources.amb_business_accounts import AsyncAmbBusinessAccounts, AmbBusinessAccounts
from bird.resources.amb_conversations_gen import AsyncAmbConversations, AmbConversations
from bird.resources.amb_routing_rules_gen import AsyncAmbRoutingRules, AmbRoutingRules
from bird.resources.amb_stats import AsyncAmbStats, AmbStats
from bird.resources.amb_suppressions_gen import AsyncAmbSuppressions, AmbSuppressions
from bird.resources.amb_templates import AsyncAmbTemplates, AmbTemplates


def _template_body(
    *,
    template: str | None,
    language: str | None,
    parameters: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if template is None and language is None and parameters is None:
        return None
    tmpl: dict[str, Any] = {}
    if template is not None:
        tmpl["id" if template.startswith("amt_") else "slug"] = template
    if language is not None:
        tmpl["language"] = language
    if parameters is not None:
        tmpl["parameters"] = parameters
    return tmpl


class Amb(AmbBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.business_accounts = AmbBusinessAccounts(client)
        self.conversations = AmbConversations(client)
        self.routing_rules = AmbRoutingRules(client)
        self.stats = AmbStats(client)
        self.suppressions = AmbSuppressions(client)
        self.templates = AmbTemplates(client)

    def send(
        self,
        *,
        from_: str,
        to: str,
        text: Mapping[str, Any] | None = None,
        rich_link: Mapping[str, Any] | None = None,
        interactive: Mapping[str, Any] | None = None,
        template: str | None = None,
        language: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        source: str | None = None,
        category: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        group: str | None = None,
        intent: str | None = None,
        locale: str | None = None,
        options: RequestOptions | None = None,
    ) -> AMBMessage:
        """Reply to an open conversation as a configured, connected business account.
        Supply ``text``, ``rich_link`` or ``interactive`` (the last two optionally
        with ``text``, sent first as its own bubble), or a stored ``template`` (by
        id or slug, with optional ``language`` and ``parameters``).

        Example:
            message = bird.amb.send(
                from_="b52d6267-2b62-4f8a-8842-0533d0f1dc07",
                to="opaque-customer",
                text={"body": "Your order is ready."},
            )
        """
        body = to_wire(AMBMessageSendRequest, {
            "from": from_, "to": to, "text": text, "rich_link": rich_link, "interactive": interactive,
            "template": _template_body(template=template, language=language, parameters=parameters),
            "source": source, "category": category, "metadata": metadata, "tags": tags,
            "group": group, "intent": intent, "locale": locale,
        })
        return self._write("POST", "/v1/amb/messages", body, AMBMessage, options)


class AsyncAmb(AsyncAmbBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.business_accounts = AsyncAmbBusinessAccounts(client)
        self.conversations = AsyncAmbConversations(client)
        self.routing_rules = AsyncAmbRoutingRules(client)
        self.stats = AsyncAmbStats(client)
        self.suppressions = AsyncAmbSuppressions(client)
        self.templates = AsyncAmbTemplates(client)

    async def send(
        self,
        *,
        from_: str,
        to: str,
        text: Mapping[str, Any] | None = None,
        rich_link: Mapping[str, Any] | None = None,
        interactive: Mapping[str, Any] | None = None,
        template: str | None = None,
        language: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        source: str | None = None,
        category: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        tags: Sequence[Mapping[str, str]] | None = None,
        group: str | None = None,
        intent: str | None = None,
        locale: str | None = None,
        options: RequestOptions | None = None,
    ) -> AMBMessage:
        """Reply to an open conversation as a configured, connected business account.
        Supply ``text``, ``rich_link`` or ``interactive`` (the last two optionally
        with ``text``, sent first as its own bubble), or a stored ``template`` (by
        id or slug, with optional ``language`` and ``parameters``).

        Example:
            message = await bird.amb.send(
                from_="b52d6267-2b62-4f8a-8842-0533d0f1dc07",
                to="opaque-customer",
                text={"body": "Your order is ready."},
            )
        """
        body = to_wire(AMBMessageSendRequest, {
            "from": from_, "to": to, "text": text, "rich_link": rich_link, "interactive": interactive,
            "template": _template_body(template=template, language=language, parameters=parameters),
            "source": source, "category": category, "metadata": metadata, "tags": tags,
            "group": group, "intent": intent, "locale": locale,
        })
        return await self._write("POST", "/v1/amb/messages", body, AMBMessage, options)


class _AmbSendRequired(TypedDict):
    from_: str
    to: str


class AmbSendParams(_AmbSendRequired, total=False):
    text: Mapping[str, Any]
    rich_link: Mapping[str, Any]
    interactive: Mapping[str, Any]
    template: str
    language: str
    parameters: Mapping[str, Any]
    source: str
    category: str
    metadata: Mapping[str, Any]
    tags: Sequence[Mapping[str, str]]
    group: str
    intent: str
    locale: str
