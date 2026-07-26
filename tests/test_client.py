from __future__ import annotations

from typing import Any

import pytest
import requests
import responses
from responses import matchers

from coverpy import CoverPy, Entity, InvalidResponseError, NoResultsError, NoResultsException

SEARCH_URL = "https://itunes.apple.com/search"
LOOKUP_URL = "https://itunes.apple.com/lookup"


@responses.activate
def test_search_returns_rich_album_result(album_item: dict[str, Any]) -> None:
    responses.get(
        SEARCH_URL,
        json={"resultCount": 1, "results": [album_item]},
        match=[
            matchers.query_param_matcher(
                {
                    "term": "OK Computer",
                    "country": "US",
                    "media": "music",
                    "entity": "album",
                    "limit": "1",
                    "explicit": "No",
                    "lang": "en_us",
                    "attribute": "albumTerm",
                }
            )
        ],
    )

    with CoverPy(timeout=3) as client:
        results = client.search(
            " OK Computer ",
            1,
            explicit=False,
            language="en_us",
            attribute="albumTerm",
        )

    result = results[0]
    assert result.name == "OK Computer"
    assert result.artist_name == "Radiohead"
    assert result.type == "album"
    assert result.release_date is not None
    assert result.release_date.isoformat() == "2016-04-01T07:00:00+00:00"
    assert result.request_url is not None
    assert "term=OK+Computer" in result.request_url


@responses.activate
def test_get_cover_preserves_legacy_behavior(song_item: dict[str, Any]) -> None:
    responses.get(SEARCH_URL, json={"resultCount": 1, "results": [song_item]})

    result = CoverPy().get_cover("Sugar", entity=Entity.SONG)

    assert result.name == "Sugar"
    assert result.artist == "Maroon 5"
    assert result.album == "V (Deluxe)"
    assert result.artworkThumb.endswith("100x100bb.jpg")
    assert result.url.startswith(SEARCH_URL)


@responses.activate
def test_get_cover_raises_both_no_result_names() -> None:
    responses.get(SEARCH_URL, json={"resultCount": 0, "results": []})

    assert NoResultsException is NoResultsError
    with pytest.raises(NoResultsException, match="Nothing"):
        CoverPy().get_cover("Nothing")


@responses.activate
def test_search_raises_http_errors() -> None:
    responses.get(SEARCH_URL, status=503)

    with pytest.raises(requests.HTTPError):
        CoverPy().search("OK Computer")


@responses.activate
@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "non-object"),
        ({}, "missing results metadata"),
        ({"resultCount": "1", "results": []}, "missing results metadata"),
        ({"resultCount": 1, "results": ["bad"]}, "invalid result object"),
    ],
)
def test_search_rejects_invalid_payloads(payload: Any, message: str) -> None:
    responses.get(SEARCH_URL, json=payload)

    with pytest.raises(InvalidResponseError, match=message):
        CoverPy().search("OK Computer")


@responses.activate
def test_search_rejects_invalid_json() -> None:
    responses.get(SEARCH_URL, body="not-json", content_type="application/json")

    with pytest.raises(InvalidResponseError, match="invalid JSON"):
        CoverPy().search("OK Computer")


@responses.activate
def test_lookup_supports_ids_and_upcs(album_item: dict[str, Any]) -> None:
    responses.get(
        LOOKUP_URL,
        json={"resultCount": 1, "results": [album_item]},
        match=[
            matchers.query_param_matcher(
                {"id": "1097861387", "country": "GB", "entity": "song", "limit": "5"}
            )
        ],
    )
    responses.get(
        LOOKUP_URL,
        json={"resultCount": 1, "results": [album_item]},
        match=[
            matchers.query_param_matcher(
                {"upc": "720642462928", "country": "US", "entity": "album"}
            )
        ],
    )

    client = CoverPy()
    by_id = client.lookup(1097861387, entity=Entity.SONG, limit=5, country="gb")
    by_upc = client.lookup_upc(" 720642462928 ", entity=Entity.ALBUM)

    assert by_id[0].collection_id == 1097861387
    assert by_upc[0].name == "OK Computer"


@pytest.mark.parametrize(
    ("call", "error", "message"),
    [
        (lambda client: client.search(""), ValueError, "term"),
        (lambda client: client.search("x", 0), ValueError, "limit"),
        (lambda client: client.search("x", 201), ValueError, "limit"),
        (lambda client: client.search("x", True), ValueError, "limit"),
        (lambda client: client.search("x", entity="book"), ValueError, "entity"),
        (lambda client: client.search("x", explicit="No"), TypeError, "explicit"),
        (lambda client: client.search("x", language="fr_fr"), ValueError, "language"),
        (lambda client: client.search("x", attribute=" "), ValueError, "attribute"),
        (lambda client: client.lookup(0), ValueError, "identifier"),
        (lambda client: client.lookup(True), ValueError, "identifier"),
        (lambda client: client.lookup_upc("abc"), ValueError, "UPC"),
    ],
)
def test_request_validation(call: Any, error: type[Exception], message: str) -> None:
    with pytest.raises(error, match=message):
        call(CoverPy())


@pytest.mark.parametrize("country", ["U", "USA", "1S", " US ", 42])
def test_country_validation(country: Any) -> None:
    with pytest.raises(ValueError, match="country"):
        CoverPy(country=country)


@pytest.mark.parametrize("timeout", [0, -1, True, "10"])
def test_timeout_validation(timeout: Any) -> None:
    with pytest.raises(ValueError, match="timeout"):
        CoverPy(timeout=timeout)


def test_external_session_is_not_closed() -> None:
    session = requests.Session()
    client = CoverPy(session=session)
    client.close()

    assert str(session.headers["User-Agent"]).startswith("coverpy")
    session.close()
