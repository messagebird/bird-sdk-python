import sys
from enum import Enum
from importlib import import_module
from pathlib import Path
from runpy import run_path
from types import ModuleType
from typing import Literal, Optional, Union

from pydantic import create_model

scripts = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts))
comparison = run_path(str(scripts / "model_diff.py"))
surface = comparison["surface"]


class Kind(str, Enum):
    first = "first"
    second = "second"


def model_module(kind: object, optional: object, open_kind: object) -> ModuleType:
    module = ModuleType("fixture")
    module.__dict__["Example"] = create_model(
        "Example",
        __module__=module.__name__,
        kind=(kind, ...),
        optional=(optional, None),
        open_kind=(open_kind, ...),
    )
    return module


def test_surface_compares_fixed_values():
    expected = surface(model_module(
        Literal["first", "second"], Optional[Literal["fixed"]], Union[Kind, str],
    ))
    equivalent = surface(model_module(
        Kind, Literal["fixed"] | None, str,
    ))
    unrestricted = surface(model_module(
        str, Optional[str], str,
    ))
    wrong_value = surface(model_module(
        Literal["different"], Literal["fixed"] | None, str,
    ))

    assert expected == equivalent
    assert expected != unrestricted
    assert expected != wrong_value


def test_component_names_exclude_unreachable_schema_collisions(monkeypatch, tmp_path):
    import yaml

    named = comparison["component_schemas"]
    generate_models = import_module("generate_models")

    path, methods = next(iter(generate_models.KEEP.items()))
    monkeypatch.setattr(generate_models, "KEEP", {path: methods})
    bundle = tmp_path / "bundle.yaml"
    bundle.write_text(yaml.safe_dump({
        "paths": {path: {next(iter(methods)): {
            "responses": {"200": {"content": {"application/json": {
                "schema": {"$ref": "#/components/schemas/Record"},
            }}}},
        }}},
        "components": {"schemas": {
            "Record": {"type": "object", "properties": {"region": {"type": "string"}}},
            "Region": {"type": "string", "enum": ["us1", "eu1"]},
            "WebhookEvent": {"type": "object"},
            "WebhookEventType": {"type": "string"},
        }},
    }))
    monkeypatch.setitem(named.__globals__, "BUNDLE", bundle)

    assert named() == {"Record", "WebhookEvent", "WebhookEventType"}
