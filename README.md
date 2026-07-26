# coverpy

[![CI](https://github.com/matteing/coverpy/actions/workflows/ci.yml/badge.svg)](https://github.com/matteing/coverpy/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/coverpy.svg)](https://pypi.org/project/coverpy/)
[![Python](https://img.shields.io/pypi/pyversions/coverpy.svg)](https://pypi.org/project/coverpy/)

`coverpy` is a small, typed Python client for finding albums, songs, artists, and artwork
through Apple's public iTunes Search API. It has no API key requirement.

> A little history: I built the original version when I was like 15, lol. This library is
> ten years old, and version 1.0 brings it back with a modern Python API and toolchain.

## Highlights

- Python 3.10+ with complete type information
- Album, song, artist, music video, and mix searches
- ID and UPC lookups
- Rich result metadata, including release dates, prices, genres, explicitness, duration,
  streamability, previews, and Store URLs
- Configurable storefront, timeout, language, explicit-content filtering, and artwork size
- A zero-setup `uvx` command-line interface
- `uv`-based development, builds, and reproducible dependency locking

## Install

Add the library to a uv project:

```console
uv add coverpy
```

Or install it with pip:

```console
python -m pip install coverpy
```

Run the CLI without installing it permanently:

```console
uvx coverpy "OK Computer" --size 1200
```

## Usage

Fetch the best album match:

```python
from coverpy import CoverPy, NoResultsError

with CoverPy(country="US") as client:
    try:
        result = client.get_cover("OK Computer")
    except NoResultsError:
        print("Nothing found.")
    else:
        print(result.name)
        print(result.artist_name)
        print(result.release_date)
        print(result.artwork(1200))
```

Search for several songs and use their expanded metadata:

```python
from coverpy import CoverPy, Entity

with CoverPy() as client:
    songs = client.search(
        "Sugar Maroon 5",
        limit=5,
        entity=Entity.SONG,
        explicit=False,
    )

for song in songs:
    print(song.name, song.duration, song.preview_url, song.store_url)
```

Look up a known catalog ID or UPC:

```python
with CoverPy() as client:
    album = client.lookup(1097861387)
    album_and_tracks = client.lookup_upc("720642462928", entity=Entity.SONG)
```

`search()` and the lookup methods return an empty list when there are no matches.
`get_cover()` keeps the original convenience behavior and raises `NoResultsError`.

### Compatibility

The original names still work: `CoverPy`, `Result`, `NoResultsException`, `result.artist`,
`result.album`, `result.type`, `result.url`, `result.artworkThumb`, and `result.artwork(size)`.
New code should prefer the snake-case fields and `NoResultsError`.

## CLI

```console
uvx coverpy "In Rainbows" --entity album --limit 3 --country GB
uvx coverpy "Everything in Its Right Place" --entity song --json
```

Use `uvx coverpy --help` for every option.

## Development

```console
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv build --no-sources
uvx --from twine twine check dist/*
```

The repository uses GitHub Actions instead of Travis CI. CI tests every supported Python
version, checks formatting, linting, typing, coverage, and verifies both wheel and source
distributions.

## Releasing

Publishing uses PyPI Trusted Publishing, so no long-lived PyPI token is stored in GitHub.

1. Configure a PyPI Trusted Publisher for `matteing/coverpy`, workflow `release.yml`, and
   environment `pypi`.
2. Update `version` in `pyproject.toml` with `uv version <version>` and update the changelog.
3. Publish a GitHub release tagged `v<version>`.

The release workflow verifies the tag, builds and smoke-tests both distributions, and then
publishes them to PyPI.

## API and artwork terms

Apple documents the iTunes Search API as rate-limited and recommends caching for heavier
usage. Artwork and previews are promotional content governed by Apple's terms. Review the
[iTunes Search API overview](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/)
before shipping them in a product.

## License

MIT
