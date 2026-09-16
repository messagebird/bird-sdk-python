from enum import Enum
from pathlib import Path
from runpy import run_path
from types import ModuleType
from typing import Literal, Optional, Union

from pydantic import create_model

surface = run_path(str(Path(__file__).resolve().parents[1] / "scripts/model_diff.py"))["surface"]


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
