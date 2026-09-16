#!/usr/bin/env python3
"""Compare two generated model modules by what they MEAN, not how they read.

The wire models are no longer byte-reproducible against the generator they
replaced: beak renders its own layout, and synthesized class names (the ones no
component schema names) differ on purpose. So a text diff says nothing. This
compares the model surface instead:

* every class both modules define, by name;
* per model, its field names, which are required, and fixed scalar values;
* per enum, its member values;
* whether each is a root model.

Other annotations are not compared: the two spell the same type differently
(``Optional[X]`` against ``X | None``). Fixed values normalize literals, enums,
and union spelling so a dropped discriminant cannot pass as an untyped field.

A class only one side defines is a failure when the ORACLE names it after a
component schema and types a field with it: that is a type a caller can be
handed and can no longer import. A synthesized name differs by design, and an
extra class on our side is not a loss — the typed IDs are root models the
oracle collapses away.

    python scripts/model_diff.py OURS THEIRS
"""

from __future__ import annotations

import enum
import importlib.util
import sys
import types
import typing
from pathlib import Path

import yaml
from pydantic import RootModel

BUNDLE = Path(__file__).resolve().parents[3] / "backend/openapi/.generated/openapi.public.bundle.yaml"


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        sys.exit(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def fixed_values(annotation: object) -> frozenset[tuple[str, str]] | None:
    origin = typing.get_origin(annotation)
    if origin is typing.Literal:
        values = typing.get_args(annotation)
    elif isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        values = tuple(member.value for member in annotation)
    elif origin in (typing.Union, types.UnionType):
        branches = [fixed_values(arg) for arg in typing.get_args(annotation) if arg is not type(None)]
        if any(branch is None for branch in branches):
            return None
        return frozenset(value for branch in branches if branch is not None for value in branch)
    else:
        return None
    return frozenset((type(value).__name__, repr(value)) for value in values if value is not None)


def surface(mod) -> dict[str, object]:
    out: dict[str, object] = {}
    for name in dir(mod):
        obj = getattr(mod, name)
        if not isinstance(obj, type) or obj.__module__ != mod.__name__:
            continue
        if issubclass(obj, enum.Enum):
            # A None member is dropped on both sides: a null in the spec's
            # value list means the field is nullable, and the generator this
            # replaces turned it into a member instead.
            out[name] = ("enum", frozenset(m.value for m in obj if m.value is not None))
        elif hasattr(obj, "model_fields"):
            fields = frozenset(
                (f.alias or key, bool(f.is_required()), fixed_values(f.annotation))
                for key, f in obj.model_fields.items()
            )
            # A root model wraps one value; a plain model that happens to
            # declare a field named `root` reads identically without this.
            out[name] = ("root" if issubclass(obj, RootModel) else "model", fields)
    return out


def component_schemas() -> frozenset[str]:
    """The names the spec itself gives its schemas, which the SDK exports."""
    if not BUNDLE.exists():
        sys.exit(f"OpenAPI bundle not found: {BUNDLE}")
    spec = yaml.safe_load(BUNDLE.read_text())
    return frozenset(spec.get("components", {}).get("schemas", {}))


def field_types(mod) -> frozenset[str]:
    """Every class named by a model field's annotation, at any depth."""
    out: set[str] = set()

    def walk(annotation: object) -> None:
        if isinstance(annotation, type):
            out.add(annotation.__name__)
            return
        for arg in typing.get_args(annotation):
            walk(arg)

    for name in dir(mod):
        obj = getattr(mod, name)
        if not isinstance(obj, type) or obj.__module__ != mod.__name__:
            continue
        for f in getattr(obj, "model_fields", {}).values():
            walk(f.annotation)
    return frozenset(out)


def one_value_enum(mod, name: str) -> bool:
    """Whether the oracle's class is a single-member enum.

    beak renders one of those as a ``Literal`` at every use and emits no class,
    so a caller reads the value off the annotation and has nothing to import.
    A vocabulary that gains a second value gets a class on both sides, and this
    stops matching.
    """
    obj = getattr(mod, name, None)
    return isinstance(obj, type) and issubclass(obj, enum.Enum) and len(list(obj)) == 1


# These exact vocabularies follow the source fields; dcg narrows the voice
# branches from their parent discriminator and over-widens the media header.
ORACLE_ANNOTATION_DIFFERENCES = {
    ("VoiceCallInboundRouteForward", "type"): (
        typing.Literal["forward", "reject", "trunk"], typing.Literal["forward"],
    ),
    ("VoiceCallInboundRouteReject", "type"): (
        typing.Literal["forward", "reject", "trunk"], typing.Literal["reject"],
    ),
    ("VoiceCallInboundRouteTrunk", "type"): (
        typing.Literal["forward", "reject", "trunk"], typing.Literal["trunk"],
    ),
    ("WhatsAppInteractiveHeaderSend2", "type"): (
        typing.Literal["image", "video", "document"],
        typing.Literal["text", "image", "video", "document"],
    ),
}


def main() -> None:
    ours_mod, theirs_mod = load(sys.argv[1], "ours"), load(sys.argv[2], "theirs")
    ours, theirs = surface(ours_mod), surface(theirs_mod)
    shared = sorted(set(ours) & set(theirs))
    problems = []
    accepted = set()
    for name in shared:
        if ours[name] != theirs[name]:
            a, b = ours[name], theirs[name]
            if a[0] != b[0]:
                problems.append(f"{name}: kind {b[0]} -> {a[0]}")
                continue
            missing, extra = set(b[1] - a[1]), set(a[1] - b[1])
            if a[0] != "enum":
                ours_fields = {field[0]: field for field in extra}
                for theirs_field in list(missing):
                    key = (name, theirs_field[0])
                    ours_field = ours_fields.get(theirs_field[0])
                    expected = ORACLE_ANNOTATION_DIFFERENCES.get(key)
                    if expected is None or ours_field is None or ours_field[:2] != theirs_field[:2]:
                        continue
                    if (ours_field[2], theirs_field[2]) == tuple(fixed_values(t) for t in expected):
                        missing.remove(theirs_field)
                        extra.remove(ours_field)
                        accepted.add(key)
            if missing:
                problems.append(f"{name}: missing {sorted(missing)}")
            if extra:
                problems.append(f"{name}: extra {sorted(extra)}")

    stale = {key for key in ORACLE_ANNOTATION_DIFFERENCES if key[0] in shared} - accepted
    if stale:
        problems.append(f"oracle annotation differences need review: {sorted(stale)}")

    only_theirs = sorted(set(theirs) - set(ours))
    only_ours = sorted(set(ours) - set(theirs))
    print(f"compared {len(shared)} shared classes ({len(ours)} ours, {len(theirs)} theirs)")
    if only_theirs:
        print(f"only in theirs ({len(only_theirs)}): {only_theirs[:20]}")
    if only_ours:
        print(f"only in ours ({len(only_ours)}): {only_ours[:20]}")

    components, reachable = component_schemas(), field_types(theirs_mod)
    dropped = [
        n
        for n in only_theirs
        if n in components and n in reachable and not one_value_enum(theirs_mod, n)
    ]
    if dropped:
        problems.append(f"{len(dropped)} component schema(s) type a field but we define no class: {dropped}")
    if problems:
        print(f"\n{len(problems)} difference(s):")
        for p in problems[:40]:
            print(f"  {p}")
        sys.exit(1)
    print("no field-level differences in the shared surface")


if __name__ == "__main__":
    main()
