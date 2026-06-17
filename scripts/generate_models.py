#!/usr/bin/env python3
"""Generate the Bird Python SDK's wire models from the OpenAPI customer bundle.

datamodel-code-generator has no operation filter, so the one thing this script
does by hand is scope the spec to the curated SDK surface (the same operations the
TS and Go SDKs expose): keep the email operations, walk every ``$ref`` they reach
— plus the webhook event union, which no operation references but
``webhooks.unwrap`` decodes — and prune the unreachable component schemas.
Everything else is native generator behavior; the per-flag rationale lives at the
call site in ``main``.

Run via ``make generate``. Regenerate after the OpenAPI bundle changes; the output
is checked in and guarded by the repo drift gate.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from surface_ops import KEEP  # generated from the surface catalog; see surface_ops.py

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT.parent.parent / "backend/openapi/.generated/openapi.public.bundle.yaml"
OUT = ROOT / "src/bird/_generated.py"

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


def main() -> None:
    if not BUNDLE.exists():
        sys.exit(f"OpenAPI bundle not found: {BUNDLE}\nRun `make openapi-bundle` from the repo root first.")

    spec = yaml.safe_load(BUNDLE.read_text())

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
            "--target-python-version", "3.10",
            "--output", str(OUT),
        ],
        check=True,
    )
    print(f"generated models into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
