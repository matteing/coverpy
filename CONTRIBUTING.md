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

The default suite mocks network access so pull requests remain deterministic. Run the
separate end-to-end suite to exercise the public iTunes API, Apple Music motion metadata,
HLS playlists, direct MP4 delivery, and the installed CLI against live services:

```console
COVERPY_RUN_E2E=1 uv run pytest -m e2e tests/e2e --no-cov
```

GitHub Actions runs these tests after relevant pushes to `master`, every Monday, and on
demand. Live failures can indicate an Apple API change rather than a CoverPy regression.
