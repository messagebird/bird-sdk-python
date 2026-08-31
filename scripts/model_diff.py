#!/usr/bin/env python3
"""Compare two generated model modules by what they MEAN, not how they read.

The wire models are no longer byte-reproducible against the generator they
replaced: beak renders its own layout, and synthesized class names (the ones no
component schema names) differ on purpose. So a text diff says nothing. This
compares the model surface instead:

* every class both modules define, by name;
* per model, its field names and which are required;
* per enum, its member values;
* whether each is a root model.

What it does NOT compare is annotations, because the two spell the same type
differently (``Optional[X]`` against ``X | None``). pyright and the SDK's own
suite cover that; this covers the thing they cannot see, which is a class or a
field silently going missing.

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
                (f.alias or key, bool(f.is_required()))
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


def main() -> None:
    ours_mod, theirs_mod = load(sys.argv[1], "ours"), load(sys.argv[2], "theirs")
    ours, theirs = surface(ours_mod), surface(theirs_mod)
    shared = sorted(set(ours) & set(theirs))
    problems = []
    for name in shared:
        if ours[name] != theirs[name]:
            a, b = ours[name], theirs[name]
            if a[0] != b[0]:
                problems.append(f"{name}: kind {b[0]} -> {a[0]}")
                continue
            missing, extra = sorted(b[1] - a[1]), sorted(a[1] - b[1])
            if missing:
                problems.append(f"{name}: missing {missing}")
            if extra:
                problems.append(f"{name}: extra {extra}")

    only_theirs = sorted(set(theirs) - set(ours))
    only_ours = sorted(set(ours) - set(theirs))
    print(f"compared {len(shared)} shared classes ({len(ours)} ours, {len(theirs)} theirs)")
    if only_theirs:
        print(f"only in theirs ({len(only_theirs)}): {only_theirs[:20]}")
    if only_ours:
        print(f"only in ours ({len(only_ours)}): {only_ours[:20]}")

    components, reachable = component_schemas(), field_types(theirs_mod)
    dropped = [n for n in only_theirs if n in components and n in reachable]
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
