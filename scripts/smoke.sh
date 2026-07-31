#!/usr/bin/env bash
# Post-publish smoke test for the messagebird-sdk PyPI package.
#
# Install the just-published version into a throwaway virtualenv and import the
# public clients. This proves the wheel installs and the package imports cleanly
# with no repo context — it catches a broken sdist/wheel, a missing module, or a
# bad dependency pin (the "published but unusable" class). Import-only by design:
# it validates packaging, not API calls (a real call would need credentials).
#
# Usage: smoke.sh <version> [index-url]
#   index-url lets the test target TestPyPI; pypi.org is added as an extra index
#   so transitive deps (pydantic, httpx) still resolve from prod.
# Called by: the mirror release workflow after publish.
set -euo pipefail
ver="${1:?usage: smoke.sh <version> [index-url]}"
index="${2:-}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

python3 -m venv "$tmp/venv"
"$tmp/venv/bin/python" -m pip install --quiet --upgrade pip

pip_args=(install --quiet "messagebird-sdk==${ver}")
if [ -n "$index" ]; then
	pip_args+=(--index-url "$index" --extra-index-url "https://pypi.org/simple/")
fi
# A just-published version can lag the index/CDN, so retry for ~5 minutes and
# print pip's own output on the last attempt: a swallowed error makes a
# propagation lag look identical to a packaging break.
attempts=10
for attempt in $(seq 1 "$attempts"); do
	if out=$("$tmp/venv/bin/python" -m pip "${pip_args[@]}" 2>&1); then
		break
	fi
	if [ "$attempt" -eq "$attempts" ]; then
		echo "smoke: messagebird-sdk==${ver} not installable after ${attempts} attempts (~5m); last error:" >&2
		printf '%s\n' "$out" | sed 's/^/  /' >&2
		exit 1
	fi
	echo "smoke: messagebird-sdk==${ver} not available yet — retrying in 30s (attempt ${attempt}/${attempts})"
	sleep 30
done

"$tmp/venv/bin/python" - <<PY
from importlib.metadata import version
from bird import Bird, AsyncBird  # public clients must import cleanly

installed = version("messagebird-sdk")
assert installed == "${ver}", f"installed {installed} != expected ${ver}"
assert Bird and AsyncBird
print(f"messagebird-sdk {installed} smoke OK")
PY
