"""Golden-vector tests for Bird-Caller detection.

Loads the shared cross-language fixtures (clients/caller-detection-cases.json) so
the Python detector stays in lockstep with the CLI and the other SDKs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bird._caller import detect_caller

_CASES = json.loads(
    (Path(__file__).resolve().parent / "caller-detection-cases.json").read_text()
)["cases"]


@pytest.mark.parametrize("case", _CASES, ids=[c["name"] for c in _CASES])
def test_detect_caller_golden(case: dict) -> None:
    assert detect_caller(case["env"]) == case["want"]
