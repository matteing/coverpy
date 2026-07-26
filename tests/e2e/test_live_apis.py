from __future__ import annotations

import json
import os
import subprocess
import sys
from urllib.parse import urlparse

import pytest
import requests

from coverpy import CoverPy

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("COVERPY_RUN_E2E") != "1",
        reason="set COVERPY_RUN_E2E=1 to call Apple's live APIs",
    ),
]

OK_COMPUTER_ID = 1097861387
MOTION_ALBUM_ID = 1693323844


def _assert_https_url(url: str | None, *, suffix: str | None = None) -> str:
    assert url is not None
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc
    if suffix is not None:
        assert parsed.path.endswith(suffix)
    return url


def test_live_search_lookup_and_static_artwork() -> None:
    with CoverPy(country="US", timeout=30) as client:
        results = client.search("OK Computer Radiohead", limit=3)
        lookup_results = client.lookup(OK_COMPUTER_ID)

    matching_album = next(
        (result for result in results if result.artist_name == "Radiohead"),
        None,
    )
    assert matching_album is not None
    assert matching_album.collection_name
    assert matching_album.type == "album"
    assert "1200x1200" in matching_album.artwork(1200)
    _assert_https_url(matching_album.store_url)

    assert lookup_results
    looked_up_album = lookup_results[0]
    assert looked_up_album.collection_id == OK_COMPUTER_ID
    assert looked_up_album.artist_name == "Radiohead"
    _assert_https_url(looked_up_album.artwork_url)


def test_live_cli_searches_and_emits_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "coverpy.cli",
            "OK Computer Radiohead",
            "--limit",
            "1",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["artist"] == "Radiohead"
    _assert_https_url(payload[0]["artwork_url"])


def test_live_motion_artwork_resolves_playable_video() -> None:
    with CoverPy(country="US", timeout=30) as client:
        artwork = client.get_motion_artwork(MOTION_ALBUM_ID)

    assert artwork is not None
    assert artwork.album_id == MOTION_ALBUM_ID
    hls_url = _assert_https_url(artwork.hls_url, suffix=".m3u8")
    _assert_https_url(artwork.tall_hls_url, suffix=".m3u8")
    video_urls = {
        _assert_https_url(artwork.video_url, suffix=".mp4"),
        _assert_https_url(artwork.hq_video_url, suffix=".mp4"),
    }

    hls_response = requests.get(hls_url, timeout=30)
    hls_response.raise_for_status()
    assert hls_response.text.startswith("#EXTM3U")

    for video_url in video_urls:
        with requests.get(
            video_url,
            headers={"Range": "bytes=0-0"},
            stream=True,
            timeout=30,
        ) as response:
            response.raise_for_status()
            assert response.status_code in {200, 206}
            assert response.headers.get("Content-Type", "").startswith("video/mp4")
            assert next(response.iter_content(chunk_size=1))
