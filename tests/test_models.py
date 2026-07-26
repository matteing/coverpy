from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from coverpy import ArtworkUnavailableError, Result


def test_song_result_exposes_normalized_metadata(song_item: dict[str, Any]) -> None:
    result = Result.from_api(song_item, request_url="https://itunes.apple.com/search?term=Sugar")

    assert result.identifier == 993352744
    assert result.type == "song"
    assert result.store_url == song_item["trackViewUrl"]
    assert result.duration == timedelta(milliseconds=235514)
    assert result.explicitness == "explicit"
    assert result.track_price == 1.29
    assert result.is_streamable is True
    assert result.raw["trackName"] == "Sugar"

    serialized = result.as_dict()
    assert serialized["name"] == "Sugar"
    assert serialized["duration_ms"] == 235514
    assert serialized["release_date"] == "2015-05-15T07:00:00+00:00"
    assert serialized["store_url"] == song_item["trackViewUrl"]


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://is1.mzstatic.com/image/thumb/Music/100x100bb.jpg",
            "https://is1.mzstatic.com/image/thumb/Music/1600x1600bb.jpg",
        ),
        (
            "https://a1.itunes.apple.com/Music/cover.100x100-75.jpg",
            "https://a1.itunes.apple.com/Music/cover.1600x1600-75.jpg",
        ),
        (
            "https://example.test/art/{w}x{h}bb.jpeg",
            "https://example.test/art/1600x1600bb.jpeg",
        ),
    ],
)
def test_artwork_resizes_known_apple_urls(url: str, expected: str) -> None:
    result = Result.from_api({"artworkUrl100": url})

    assert result.artwork(1600) == expected


@pytest.mark.parametrize("size", [0, -1, 1.5, True])
def test_artwork_rejects_invalid_sizes(size: Any) -> None:
    result = Result.from_api({"artworkUrl100": "https://example.test/100x100bb.jpg"})

    with pytest.raises(ValueError, match="positive integer"):
        result.artwork(size)


def test_artwork_reports_missing_data() -> None:
    with pytest.raises(ArtworkUnavailableError, match="unknown"):
        Result.from_api({}).artwork()


@pytest.mark.parametrize(
    ("item", "expected_type", "expected_name"),
    [
        ({"wrapperType": "track", "trackName": "Song"}, "song", "Song"),
        ({"wrapperType": "collection", "collectionName": "Album"}, "album", "Album"),
        ({"wrapperType": "artist", "artistName": "Artist"}, "artist", "Artist"),
        ({"wrapperType": "unknown"}, "unknown", "unknown"),
        ({"collectionType": "Album", "collectionName": "Album"}, "album", "Album"),
        ({"kind": "Music-Video", "trackName": "Video"}, "music-video", "Video"),
    ],
)
def test_result_type_and_name_fallbacks(
    item: dict[str, Any], expected_type: str, expected_name: str
) -> None:
    result = Result.from_api(item)

    assert result.type == expected_type
    assert result.name == expected_name


def test_result_tolerates_unexpected_optional_values() -> None:
    result = Result.from_api(
        {
            "artistId": True,
            "collectionPrice": "free",
            "releaseDate": "not-a-date",
            "isStreamable": "yes",
            "trackTimeMillis": None,
        }
    )

    assert result.artist_id is None
    assert result.collection_price is None
    assert result.release_date is None
    assert result.is_streamable is None
    assert result.duration is None
    assert result.artist == "unknown"
    assert result.album == "unknown"
    assert result.url == ""
    assert result.artworkThumb == ""
