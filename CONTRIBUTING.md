# Contributing

## Setup

Install [uv](https://docs.astral.sh/uv/) and sync the locked environment:

```console
uv sync --locked
```

## Checks

Run the same checks as CI before opening a pull request:

```console
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv build --no-sources
uvx --from twine twine check dist/*
```

Tests must mock network access. Do not depend on the live Apple endpoint in the test suite.
