# Bird Python SDK (ADR-0045) — local dev targets. Mirrors clients/sdk-go/Makefile.
.PHONY: sync generate test lint typecheck build check-dist

sync:  ## install the package and dev dependencies into a local venv
	uv sync --extra dev

# Not a uv task any more: generation left the Python toolchain.
generate:  ## regenerate src/bird/_generated from the OpenAPI customer bundle (in-process Go)
	../../tools/bin/beak run clients:sdk-python-generate

test:
	uv run --extra dev pytest

lint:
	uv run --extra dev ruff check .

typecheck:
	uv run --extra dev pyright

build:
	uv build

check-dist:  ## build the wheel + sdist and validate the package metadata
	uv build
	uvx twine check dist/*
