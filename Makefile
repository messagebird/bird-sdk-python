# Bird Python SDK (ADR-0045) — local dev targets. Mirrors clients/sdk-go/Makefile.
.PHONY: sync generate test lint typecheck build check-dist

sync:  ## install the package and dev dependencies into a local venv
	uv sync --extra dev

generate:  ## regenerate src/bird/_generated from the OpenAPI customer bundle
	uv run --with pyyaml python scripts/generate_models.py

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
