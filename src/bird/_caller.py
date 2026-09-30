"""Bird-Caller association and self-reported execution evidence.

Best-effort, non-authoritative usage telemetry -- it only labels traffic, never
gates behavior. The single source of truth is ``clients/caller-detection.yaml``
(shared with the CLI and the other SDKs); the ordered rule table in
``_caller_rules`` is generated from it.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping

from ._caller_rules import (
    CALLER_BOOLEANISH_SKIP,
    CALLER_DEFAULT,
    CALLER_FALSE_LIKE,
    CALLER_MODEL_ENV,
    CALLER_PUBLIC_MODELS,
    CALLER_RULES,
)

_VALID = re.compile(r"^[a-z0-9._-]+$")


def detect_caller_info(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    env = os.environ if environ is None else environ
    for rule in CALLER_RULES:
        value = env.get(str(rule["env"]), "")
        equals = rule.get("equals")
        if (
            not value.strip()
            or value.strip().lower() in CALLER_FALSE_LIKE
            or (equals is not None and value != equals)
        ):
            continue
        name = _sanitize(value) if rule.get("passthrough") else str(rule["name"])
        if name:
            model_env = CALLER_MODEL_ENV.get(name, "")
            model = _normalize_model(env.get(model_env, "")) if model_env else ""
            return {
                "model": model,
                "model_source": "env:" + model_env if model else "",
                "name": name,
                "source": "env:" + str(rule["env"]),
                "execution": str(rule["execution"])
                if rule["verification"] == "verified"
                else "unknown",
            }
    return {
        "name": CALLER_DEFAULT,
        "source": "fallback",
        "execution": "unknown",
        "model": "",
        "model_source": "",
    }


def _sanitize(value: str) -> str:
    # Lowercase and bound a passthrough (AGENT=<name>) value the same charset+length
    # way as the other Bird-* labels; drop boolean-ish values with no harness identity.
    s = value.strip().lower()
    if not s or len(s) > 32 or s in CALLER_BOOLEANISH_SKIP:
        return ""
    return s if _VALID.match(s) else ""


def _normalize_model(raw: str) -> str:
    model = raw.strip().lower()
    if not model:
        return ""
    return model if model in CALLER_PUBLIC_MODELS else "other"


def client_enrichment_disabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return (
        bool(env.get("DO_NOT_TRACK"))
        or env.get("BIRD_TELEMETRY") == "0"
        or env.get("BIRD_CLIENT_ENRICHMENT") == "0"
    )
