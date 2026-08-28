#!/usr/bin/env python3
"""Generate the Bird Python SDK's wire models from the OpenAPI customer bundle.

Two things this script does by hand, everything else being native generator
behavior whose per-flag rationale lives at the call site in ``main``:

1. **Scoping.** datamodel-code-generator has no operation filter, so the spec is
   narrowed to the curated SDK surface (the same operations the TS and Go SDKs
   expose): keep the email operations, walk every ``$ref`` they reach — plus the
   webhook event union, which no operation references but ``webhooks.unwrap``
   decodes — and prune the unreachable component schemas.
2. **Open-enum retyping.** ``x-extensible-enum`` is a Bird extension the generator
   does not understand, so ``open_enum_unions`` rewrites those fields and
   ``prefer_enum_member`` fixes the resulting union's mode. Both are documented in
   AGENTS.md § "Open enums are retyped, and must stay open"; both are load-bearing
   for forward compatibility, and ``tests/test_open_enums.py`` pins them.

Run via ``make generate``. Regenerate after the OpenAPI bundle changes; the output
is checked in and guarded by the repo drift gate.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from surface_ops import KEEP  # generated from the surface catalog; see surface_ops.py

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT.parent.parent / "backend/openapi/.generated/openapi.public.bundle.yaml"
# Under beak, codegen writes to the per-run stage; beak sweeps it back.
_STAGE = os.environ.get("BEAK_STAGE")
OUT = (
    Path(_STAGE) / "clients/sdk-python/src/bird/_generated.py"
    if _STAGE
    else ROOT / "src/bird/_generated.py"
)

HTTP_METHODS = {"get", "put", "post", "delete", "patch", "options", "head", "trace"}

# Referenced by no operation, but webhooks.unwrap decodes them: the event union
# and its discriminant enum. Endpoint CRUD is not in this release, so its schemas
# are unreachable and pruned.
EXTRA_SCHEMAS = ["WebhookEvent", "WebhookEventType"]

# Wire string-formats kept as plain `str` rather than special Pydantic types
# (datetime, UUID, AnyUrl). RFC 3339 timestamps as strings is the ADR-0045 / TS
# posture; it also keeps deps at pydantic+httpx and sidesteps invalid string
# constraints on non-str types.
STRING_FORMATS = ["email", "date-time", "date", "time", "duration", "uuid", "uri", "uri-reference"]


def resolve(spec: dict, pointer: str):
    node = spec
    for part in pointer.lstrip("#/").split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def collect_refs(spec: dict) -> set[str]:
    """Every local `$ref` reachable from the kept paths plus EXTRA_SCHEMAS."""
    reached: set[str] = set()
    pending: list[str] = []

    def visit(node) -> None:
        if isinstance(node, dict):
            for key, val in node.items():
                is_local_ref = key == "$ref" and isinstance(val, str) and val.startswith("#/")
                if is_local_ref and val not in reached:
                    reached.add(val)
                    pending.append(val)
                else:
                    visit(val)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(spec["paths"])
    for name in EXTRA_SCHEMAS:
        ref = f"#/components/schemas/{name}"
        reached.add(ref)
        pending.append(ref)
    while pending:
        visit(resolve(spec, pending.pop()))
    return reached


def find_open_enums(schemas: dict) -> set[str]:
    """Names of the string schemas carrying ``x-extensible-enum`` values."""
    return {
        name
        for name, schema in schemas.items()
        if isinstance(schema, dict)
        and schema.get("type") == "string"
        and schema.get("x-extensible-enum")
    }


def open_enum_unions(spec: dict) -> list[str]:
    """Retype every open-enum field to ``<Enum> | str``, in place.

    An open enum (``x-extensible-enum``) is a plain string on the wire whose known
    values the generator cannot see, so a field referencing one lands as bare
    ``str`` and the values are lost. Giving the component a real ``enum`` makes
    datamodel-codegen emit the class, and rewriting each reference to
    ``anyOf: [<enum>, string]`` keeps the field open: a value no version of the
    spec knew about still decodes, where a bare enum field would raise.

    Generator-facing only — this runs on the filtered copy, never on the published
    bundle, which must keep saying the enum is open.

    Returns the enum class names, for the union-mode pass over the output. Empty is
    a legitimate answer: the curated surface may not reach any open enum, and the
    convention itself is asserted against the unpruned bundle in ``main``.
    """
    schemas = spec.get("components", {}).get("schemas", {})
    open_enums = find_open_enums(schemas)
    if not open_enums:
        return []

    for name in open_enums:
        # The class only exists if the component carries `enum`. The values stay
        # identical to x-extensible-enum, so the enum members are the known set.
        schemas[name]["enum"] = list(schemas[name]["x-extensible-enum"])

    ref_targets = {f"#/components/schemas/{name}" for name in open_enums}

    def rewrite(node) -> None:
        """Wrap every `$ref` to an open enum in an `anyOf` with a bare string.

        Skips the component definitions themselves (walked from `properties` and
        composition lists only), so an enum is never wrapped in its own union.
        """
        if isinstance(node, dict):
            for key, val in list(node.items()):
                if isinstance(val, dict) and val.get("$ref") in ref_targets:
                    node[key] = _open_union(val)
                else:
                    rewrite(val)
        elif isinstance(node, list):
            for i, val in enumerate(node):
                if isinstance(val, dict) and val.get("$ref") in ref_targets:
                    node[i] = _open_union(val)
                else:
                    rewrite(val)

    for name, schema in schemas.items():
        if name in open_enums:
            continue  # the enum component itself stays a plain enum
        rewrite(schema)
    rewrite(spec["paths"])
    return sorted(open_enums)


def _open_union(ref_node: dict) -> dict:
    """`{$ref: Enum, description: …}` -> `{anyOf: [{$ref: Enum}, {type: string}], description: …}`.

    Sibling keys (description, example) are carried over, so the field keeps its
    docs; the enum is listed first so the union-mode pass can prefer it.
    """
    siblings = {k: v for k, v in ref_node.items() if k != "$ref"}
    return {"anyOf": [{"$ref": ref_node["$ref"]}, {"type": "string"}], **siblings}


def main() -> None:
    if not BUNDLE.exists():
        sys.exit(f"OpenAPI bundle not found: {BUNDLE}\nRun `make openapi-bundle` from the repo root first.")

    spec = yaml.safe_load(BUNDLE.read_text())

    # Convention tripwire, asserted before pruning: the bundle always carries open
    # enums, so none at all means x-extensible-enum went away and the retype below
    # would silently no-op. After pruning, an empty set is legitimate instead — the
    # curated surface need not reach one.
    if not find_open_enums(spec.get("components", {}).get("schemas", {})):
        sys.exit("no x-extensible-enum schemas in the bundle; the convention changed")

    # Prune paths to the kept (path, method) pairs.
    kept_paths = {}
    for path, methods in KEEP.items():
        item = spec["paths"].get(path)
        if item is None:
            sys.exit(f"path not in bundle: {path}")
        kept_paths[path] = {k: v for k, v in item.items() if k not in HTTP_METHODS or k in methods}
    spec["paths"] = kept_paths

    # Prune component schemas to those reachable from the kept paths.
    reached = collect_refs(spec)
    for section, entries in list(spec.get("components", {}).items()):
        if section == "securitySchemes" or not isinstance(entries, dict):
            continue  # securitySchemes is referenced by the global `security` by name, not $ref
        kept = {name: val for name, val in entries.items() if f"#/components/{section}/{name}" in reached}
        if kept:
            spec["components"][section] = kept
        else:
            del spec["components"][section]

    open_enums = open_enum_unions(spec)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(spec, f, sort_keys=False)
        filtered = f.name

    subprocess.run(
        [
            # Pin the generator AND its formatter (black) so the checked-in output is
            # reproducible across environments — the CI drift gate regenerates and diffs it.
            "uvx", "--from", "datamodel-code-generator==0.59.0", "--with", "black==26.5.1", "datamodel-codegen",
            "--input", filtered,
            "--input-file-type", "openapi",
            "--output-model-type", "pydantic_v2.BaseModel",
            # Generated models inherit bird._models.BaseModel.
            "--base-class", "bird._models.BaseModel",
            # Forward-compatible models: a new server field never breaks a client (ADR-0045).
            "--extra-fields", "allow",
            # Flatten typed-ID RootModels (EmailID, …) to plain str, so
            # `message.id` is a string — the cross-SDK "IDs are strings" stance.
            "--collapse-root-models",
            # Fixed header so the checked-in output is byte-stable across runs (the
            # default header stamps the temp filename + a timestamp).
            "--custom-file-header", "# Generated by scripts/generate_models.py from the Bird OpenAPI bundle — do not edit.",
            # Keep wire string-formats as plain str (RFC 3339 timestamps as strings per
            # ADR-0045, plus ids/uris); also keeps runtime deps at pydantic + httpx.
            "--type-mappings", *[f"string+{fmt}=string" for fmt in STRING_FORMATS],
            # Value enums as str-subclass (`class Status(str, Enum)`), so the natural
            # idiom `msg.status == "delivered"` is both true at runtime and type-checks —
            # parity with Go's typed string constants and TS's string unions.
            "--use-subclass-enum",
            "--use-annotated",
            # typing.List/Dict rather than PEP 585 builtins. A wire property named
            # `list` binds that name in the model's class body, and PEP 563 defers
            # annotations, so pydantic resolves every SIBLING `list[...]` against the
            # shadowed name and the whole module fails to import. Nothing else in the
            # toolchain sees it, so the wire name would otherwise have to dodge every
            # builtin.
            "--no-use-standard-collections",
            "--target-python-version", "3.10",
            "--output", str(OUT),
        ],
        check=True,
    )
    prefer_enum_member(OUT, open_enums)
    print(f"generated models into {OUT.relative_to(ROOT) if not _STAGE else OUT}")


# The generator writes each open-enum field as `Enum | str`, which pydantic
# validates in smart mode: it returns a plain `str` even for a value the enum
# knows, so reading a field never yields the enum member. Left-to-right tries the
# enum first, so a known value arrives as the member (narrowing, completion) and
# an unknown one still falls through to `str`.
UNION_MODE = 'Annotated[Union[{enum}, str], Field(union_mode="left_to_right")]'


def prefer_enum_member(out: Path, open_enums: list[str]) -> None:
    """Rewrite each `Enum | str` union to prefer the enum member, then reformat.

    Annotating the union itself rather than the field is what makes this compose:
    the union also appears inside `list[...]`, where a field-level
    ``Field(union_mode=…)`` would bind to the list and never reach the element.

    A no-op when the scoped spec reached no open enum; only a retype that produced
    no union is an error, since that means the shape it keys on moved.
    """
    if not open_enums:
        return
    src = out.read_text()
    rewritten = 0
    for enum in open_enums:
        pattern = re.compile(rf"\b{re.escape(enum)} \| str\b")
        src, n = pattern.subn(UNION_MODE.format(enum=enum), src)
        rewritten += n
    if rewritten == 0:
        sys.exit(
            "no `<Enum> | str` unions in the generated models: the open-enum spec "
            "transform or the generator's union rendering changed"
        )
    # Union is not in the generator's import line; Annotated and Field already are.
    src = src.replace(
        "from typing import Annotated", "from typing import Annotated, Union", 1
    )
    out.write_text(src)
    # The rewrite changes line lengths, so reformat with the pinned formatter the
    # generator itself used — the checked-in output has to stay byte-reproducible.
    subprocess.run(
        ["uvx", "--from", "black==26.5.1", "black", "--quiet", str(out)], check=True
    )
    print(f"preferred the enum member in {rewritten} open-enum unions")


if __name__ == "__main__":
    main()
