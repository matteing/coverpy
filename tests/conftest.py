from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def album_item() -> dict[str, Any]:
    return {
        "wrapperType": "collection",
        "collectionType": "Album",
        "artistId": 657515,
        "collectionId": 1097861387,
        "artistName": "Radiohead",
        "collectionName": "OK Computer",
        "artistViewUrl": "https://music.apple.com/us/artist/radiohead/657515",
        "collectionViewUrl": "https://music.apple.com/us/album/ok-computer/1097861387",
        "artworkUrl60": "https://is1.mzstatic.com/image/thumb/Music/60x60bb.jpg",
        "artworkUrl100": "https://is1.mzstatic.com/image/thumb/Music/100x100bb.jpg",
        "collectionPrice": 9.99,
        "collectionExplicitness": "notExplicit",
        "trackCount": 12,
        "copyright": "℗ 2016 XL Recordings",
        "country": "USA",
        "currency": "USD",
        "releaseDate": "2016-04-01T07:00:00Z",
        "primaryGenreName": "Alternative",
    }


@pytest.fixture
def song_item() -> dict[str, Any]:
    return {
        "wrapperType": "track",
        "kind": "song",
        "artistId": 1798556,
        "collectionId": 993352739,
        "trackId": 993352744,
        "artistName": "Maroon 5",
        "collectionName": "V (Deluxe)",
        "trackName": "Sugar",
        "artistViewUrl": "https://music.apple.com/us/artist/maroon-5/1798556",
        "collectionViewUrl": "https://music.apple.com/us/album/v-deluxe/993352739",
        "trackViewUrl": "https://music.apple.com/us/album/v-deluxe/993352739?i=993352744",
        "previewUrl": "https://audio-ssl.itunes.apple.com/sugar.m4a",
        "artworkUrl30": "https://is1.mzstatic.com/image/thumb/Music/30x30bb.jpg",
        "artworkUrl60": "https://is1.mzstatic.com/image/thumb/Music/60x60bb.jpg",
        "artworkUrl100": "https://is1.mzstatic.com/image/thumb/Music/100x100bb.jpg",
        "collectionPrice": 12.99,
        "trackPrice": 1.29,
        "releaseDate": "2015-05-15T07:00:00Z",
        "collectionExplicitness": "explicit",
        "trackExplicitness": "explicit",
        "discCount": 1,
        "discNumber": 1,
        "trackCount": 15,
        "trackNumber": 5,
        "trackTimeMillis": 235514,
        "country": "USA",
        "currency": "USD",
        "primaryGenreName": "Pop",
        "contentAdvisoryRating": "Explicit",
        "isStreamable": True,
    }
