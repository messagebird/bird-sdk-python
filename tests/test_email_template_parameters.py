"""Template parameter discovery keeps every record it is served.

The conformance corpus only proves the populated body decodes. The base model
sets ``extra="allow"``, so a field the model failed to declare would still come
back from ``model_dump`` as extra data; asserting ``model_extra`` is empty is what
proves each field reached its declared attribute.
"""

from __future__ import annotations

import copy
from typing import Any

import httpx
import respx
from pydantic import BaseModel

from bird import (
    Bird,
    EmailTemplateParameters,
    EmailTemplateParameterType,
    EmailTemplateParameterValueDomain,
    EmailTemplateUseKind,
    EmailTemplateUseSite,
    EmailTemplateVariableSource,
)
from bird import _generated

BASE = "https://eu1.platform.bird.com"
TEMPLATE = "emt_01krdgeqcxet5s7t44vh8rt9mg"
PATH = f"{BASE}/v1/email/templates/{TEMPLATE}/parameters"

# The populated body of the email.templates.parameters conformance vector.
POPULATED: dict[str, Any] = {
    "template_id": TEMPLATE,
    "observed_version_id": "emv_01krdgeqcxet5s7t44vh8rt9mh",
    "requested_language": "en",
    "effective_language": "en",
    "requirements_fingerprint": "sha256:98603c0e927a4aac43b86f6bac4d2d3f72d6b79260aa1d3da33d18e0fea82522",
    "parameters": [
        {
            "name": "items", "type": "text", "value_domain": "scalar", "required": True, "sensitive": False,
            "use_constraints": [{"kind": "iterable", "site": "html", "path": "items", "operation": "for"}],
        },
        {
            "name": "offer", "type": "text", "value_domain": "scalar", "required": True, "sensitive": False,
            "use_constraints": [
                {"kind": "value", "site": "subject", "path": "offer", "operation": "output"},
                {"kind": "value", "site": "html", "path": "offer", "operation": "if"},
            ],
        },
        {
            "name": "order_total", "type": "amount", "value_domain": "scalar", "required": False, "sensitive": False,
            "use_constraints": [{"kind": "value", "site": "text", "path": "order_total", "operation": "output"}],
        },
    ],
    "variables": [
        {
            "path": "bird.contact.first_name", "source": "contact", "source_type": "string",
            "use_constraints": [
                {"kind": "value", "site": "subject", "path": "bird.contact.first_name", "operation": "output"},
            ],
        },
        {
            "path": "bird.unsubscribe_url", "source": "bird",
            "use_constraints": [{"kind": "value", "site": "html", "path": "bird.unsubscribe_url", "operation": "output"}],
        },
    ],
}


def _models(model: BaseModel) -> list[BaseModel]:
    found = [model]
    for name in type(model).model_fields:
        value = getattr(model, name)
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, BaseModel):
                found.extend(_models(item))
    return found


def _fetch(body: dict[str, Any], language: str | None = None) -> tuple[EmailTemplateParameters, respx.Route]:
    route = respx.get(PATH).mock(return_value=httpx.Response(200, json=body))
    return Bird(api_key="bk_eu1_secret").email.templates.parameters(TEMPLATE, language=language), route


@respx.mock
def test_populated_result_keeps_every_record() -> None:
    result, route = _fetch(POPULATED, language="en")

    assert route.calls.last.request.url.params["language"] == "en"
    assert isinstance(result, EmailTemplateParameters)
    assert result.model_dump(mode="json", exclude_unset=True) == POPULATED
    models = _models(result)
    assert len(models) == 1 + 3 + 4 + 2 + 2
    for model in models:
        assert not model.model_extra, f"{type(model).__name__} kept {model.model_extra} as undeclared extras"

    items, offer, total = result.parameters
    assert items.use_constraints[0].kind == EmailTemplateUseKind.ITERABLE
    assert items.use_constraints[0].kind is _generated.EmailTemplateUseKind.iterable
    assert [use.site for use in offer.use_constraints] == [EmailTemplateUseSite.SUBJECT, EmailTemplateUseSite.HTML]
    assert offer.use_constraints[1].operation == "if"
    assert total.type is _generated.EmailTemplateParameterType.amount
    assert total.type == EmailTemplateParameterType.AMOUNT
    assert total.value_domain == EmailTemplateParameterValueDomain.SCALAR
    assert total.required is False

    contact, unsubscribe = result.variables
    assert contact.source is _generated.EmailTemplateVariableSource.contact
    assert contact.source_type == "string"
    assert unsubscribe.source == EmailTemplateVariableSource.BIRD
    assert unsubscribe.source_type is None
    assert unsubscribe.use_constraints is not None
    assert unsubscribe.use_constraints[0].site == EmailTemplateUseSite.HTML


@respx.mock
def test_unknown_enum_values_decode_and_round_trip() -> None:
    """Every enum in the result is open: a newer server's value must not raise."""
    body = copy.deepcopy(POPULATED)
    del body["requested_language"]
    body["parameters"] = [
        {
            "name": "link", "type": "url", "value_domain": "list", "required": True, "sensitive": False,
            "use_constraints": [{"kind": "partial", "site": "amp", "path": "link"}],
        },
    ]
    body["variables"] = [{"path": "bird.workspace.name", "source": "workspace"}]

    result, route = _fetch(body)

    assert "language" not in route.calls.last.request.url.params
    parameter = result.parameters[0]
    use = parameter.use_constraints[0]
    variable = result.variables[0]
    for value, enum, wire in [
        (parameter.type, _generated.EmailTemplateParameterType, "url"),
        (parameter.value_domain, _generated.EmailTemplateParameterValueDomain, "list"),
        (use.kind, _generated.EmailTemplateUseKind, "partial"),
        (use.site, _generated.EmailTemplateUseSite, "amp"),
        (variable.source, _generated.EmailTemplateVariableSource, "workspace"),
    ]:
        assert value == wire
        assert not isinstance(value, enum)
    assert result.model_dump(mode="json", exclude_unset=True) == body
