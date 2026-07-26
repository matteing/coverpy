# Changelog

All notable changes to coverpy are documented here.

## [1.1.0] - 2026-07-25

### Added

- Experimental Apple Music motion artwork lookup for albums and search results.
- Square and tall HLS URLs plus browser-friendly standard and high-quality direct MP4 URLs.
- A `--motion` CLI option for human-readable and JSON output.

### Changed

- Prefer H.264 motion artwork variants over HEVC for wider browser compatibility.

## [1.0.0] - 2026-07-25

### Added

- A typed, context-managed Python 3.10+ client.
- Multi-result search, catalog ID lookup, and UPC lookup APIs.
- Rich normalized metadata for current iTunes Search API responses.
- A `coverpy` command suitable for one-off use through `uvx`.
- GitHub Actions for tests, package verification, and trusted PyPI publishing.

### Changed

- Replaced `setup.py`, ad hoc requirements, and Make targets with `pyproject.toml`, `uv`,
  `uvx`, and `uv.lock`.
- Moved the package to a modern `src/` layout.
- Replaced Travis CI with GitHub Actions.
- Made album search the default while retaining the original `get_cover()` API.

### Removed

- Python 2 compatibility metadata and legacy universal wheels.
- Travis, Scrutinizer, stale packaging files, and committed `.DS_Store` files.
