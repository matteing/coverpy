from __future__ import annotations

import base64
import json
from typing import Any

import pytest
import requests
import responses
from responses import matchers

from coverpy import CoverPy, MotionArtworkError, Result
from coverpy.motion import MotionArtworkResolver

TOKEN_PAGE_URL = "https://music.apple.com/us/album/1693323844"
SCRIPT_URL = "https://music.apple.com/assets/index~test.js"
ALBUM_URL = "https://amp-api.music.apple.com/v1/catalog/us/albums/1097861387"
HLS_URL = "https://video.example/master.m3u8"
TALL_HLS_URL = "https://video.example/tall.m3u8"


def _encode(value: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")


def _token(issuer: str = "AMPWebPlay", *, expiry: Any = 4_000_000_000) -> str:
    return f"{_encode({'alg': 'none'})}.{_encode({'iss': issuer, 'exp': expiry})}.signature"


def _register_token(*, script: str | None = None) -> str:
    token = _token()
    responses.get(TOKEN_PAGE_URL, body='<script src="/assets/index~test.js"></script>')
    responses.get(SCRIPT_URL, body=script or f"{_token('SomethingElse')} {token}")
    return token


def _register_album(editorial_video: Any) -> None:
    responses.get(
        ALBUM_URL,
        json={"data": [{"attributes": {"editorialVideo": editorial_video}}]},
        match=[matchers.query_param_matcher({"extend": "editorialVideo"})],
    )


def _register_hls() -> None:
    responses.get(
        HLS_URL,
        body="""#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=400000,RESOLUTION=360x360,CODECS="avc1.4d401e"
low/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1200000,RESOLUTION=640x640,CODECS="avc1.4d401f,mp4a.40.2"
standard/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=8000000,RESOLUTION=2160x2160,CODECS="hvc1.2.4.L153.B0"
hevc/playlist.m3u8
#EXT-X-STREAM-INF:AVERAGE-BANDWIDTH=5000000,RESOLUTION=1920x1920,CODECS="avc1.640033"
hq/playlist.m3u8
""",
    )
    responses.get(
        "https://video.example/standard/playlist.m3u8",
        body='#EXTM3U\n#EXT-X-MAP:URI="cover-standard.mp4",BYTERANGE="897@0"',
    )
    responses.get(
        "https://video.example/hq/playlist.m3u8",
        body="#EXTM3U\n#EXTINF:10,\n../files/cover-hq.mp4",
    )


@responses.activate
def test_get_motion_artwork_resolves_browser_compatible_videos() -> None:
    token = _register_token()
    _register_album(
        {
            "motionSquareVideo1x1": {"video": HLS_URL},
            "motionTallVideo3x4": {"video": TALL_HLS_URL},
        }
    )
    _register_hls()

    with CoverPy() as client:
        artwork = client.get_motion_artwork(Result(collection_id=1097861387))

    assert artwork is not None
    assert artwork.album_id == 1097861387
    assert artwork.hls_url == HLS_URL
    assert artwork.tall_hls_url == TALL_HLS_URL
    assert artwork.video_url == "https://video.example/standard/cover-standard.mp4"
    assert artwork.hq_video_url == "https://video.example/files/cover-hq.mp4"
    assert artwork.as_dict()["album_id"] == 1097861387
    album_request = next(
        call.request for call in responses.calls if (call.request.url or "").startswith(ALBUM_URL)
    )
    assert album_request.headers["Authorization"] == f"Bearer {token}"
    assert album_request.headers["Origin"] == "https://music.apple.com"
    assert not any("hevc/playlist.m3u8" in (call.request.url or "") for call in responses.calls)


@responses.activate
def test_get_motion_artwork_caches_web_token_and_uses_storefront() -> None:
    _register_token()
    gb_url = "https://amp-api.music.apple.com/v1/catalog/gb/albums/1097861387"
    responses.get(
        gb_url,
        json={"data": [{"attributes": {"editorialVideo": None}}]},
        match=[matchers.query_param_matcher({"extend": "editorialVideo"})],
    )

    client = CoverPy()
    assert client.get_motion_artwork("1097861387", storefront="GB") is None
    assert client.get_motion_artwork(1097861387, storefront="gb") is None

    assert sum(call.request.url == TOKEN_PAGE_URL for call in responses.calls) == 1


@responses.activate
def test_get_motion_artwork_supports_fallback_fields_and_media_playlist() -> None:
    _register_token()
    _register_album(
        {
            "motionDetailSquare": {"video": HLS_URL},
            "motionDetailTall": {"video": TALL_HLS_URL},
        }
    )
    responses.get(HLS_URL, body='#EXTM3U\n#EXT-X-MAP:URI="single.mp4"')

    artwork = CoverPy().get_motion_artwork(1097861387)

    assert artwork is not None
    assert artwork.video_url == "https://video.example/single.mp4"
    assert artwork.hq_video_url == artwork.video_url
    assert artwork.tall_hls_url == TALL_HLS_URL


@responses.activate
@pytest.mark.parametrize(
    "editorial_video",
    [None, {}, {"motionSquareVideo1x1": {}}, {"motionSquareVideo1x1": {"video": ""}}],
)
def test_get_motion_artwork_returns_none_when_unavailable(editorial_video: Any) -> None:
    _register_token()
    _register_album(editorial_video)

    assert CoverPy().get_motion_artwork(1097861387) is None


@pytest.mark.parametrize("album", [Result(), 0, True, "not-an-id"])
def test_get_motion_artwork_validates_album(album: Any) -> None:
    with pytest.raises(ValueError, match=r"collection ID|identifier"):
        CoverPy().get_motion_artwork(album)


@responses.activate
@pytest.mark.parametrize(
    ("page", "script", "message"),
    [
        ("no script", "", "web bundle"),
        ('<script src="/assets/index~test.js"></script>', "no token", "web token"),
        ('<script src="/assets/index~test.js"></script>', _token("SomethingElse"), "web token"),
    ],
)
def test_get_motion_artwork_rejects_missing_web_credentials(
    page: str, script: str, message: str
) -> None:
    responses.get(TOKEN_PAGE_URL, body=page)
    if "index" in page:
        responses.get(SCRIPT_URL, body=script)

    with pytest.raises(MotionArtworkError, match=message):
        CoverPy().get_motion_artwork(1097861387)


@responses.activate
@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("not-json", "invalid album JSON"),
        ({}, "missing album data"),
        ({"data": ["bad"]}, "invalid album data"),
        ({"data": [{}]}, "missing album attributes"),
        (
            {"data": [{"attributes": {"editorialVideo": "bad"}}]},
            "invalid motion artwork data",
        ),
    ],
)
def test_get_motion_artwork_rejects_invalid_album_responses(payload: Any, message: str) -> None:
    _register_token()
    if isinstance(payload, str):
        responses.get(ALBUM_URL, body=payload, content_type="application/json")
    else:
        responses.get(ALBUM_URL, json=payload)

    with pytest.raises(MotionArtworkError, match=message):
        CoverPy().get_motion_artwork(1097861387)


@responses.activate
def test_get_motion_artwork_returns_none_for_empty_catalog_data() -> None:
    _register_token()
    responses.get(ALBUM_URL, json={"data": []})

    assert CoverPy().get_motion_artwork(1097861387) is None


@responses.activate
def test_motion_resolver_uses_non_h264_and_low_quality_fallbacks() -> None:
    _register_token()
    _register_album({"motionSquareVideo1x1": {"video": HLS_URL}})
    responses.get(
        HLS_URL,
        body="""#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=100,RESOLUTION=100x100,CODECS="hvc1"
low.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=200,RESOLUTION=200x200,CODECS="hvc1"
middle.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=300,RESOLUTION=300x300,CODECS="hvc1"
high.m3u8
""",
    )
    responses.get("https://video.example/middle.m3u8", body="#EXTM3U")
    responses.get("https://video.example/high.m3u8", body='#EXT-X-MAP:URI="high.mp4"')

    artwork = CoverPy().get_motion_artwork(1097861387)

    assert artwork is not None
    assert artwork.video_url is None
    assert artwork.hq_video_url == "https://video.example/high.mp4"


def test_motion_helpers_handle_expiry_and_invalid_playlist_data() -> None:
    session = requests.Session()
    resolver = MotionArtworkResolver(session, 1)
    invalid_expiry_token = _token(expiry="later")
    assert resolver._decode_token_payload(invalid_expiry_token)["iss"] == "AMPWebPlay"
    assert resolver._decode_token_payload("eyJbad.bad.bad") == {}
    assert resolver._parse_master_playlist(HLS_URL, "#EXT-X-STREAM-INF:BANDWIDTH=nope") == []
    assert resolver._direct_video_url(HLS_URL, "#EXTM3U\nsegment.ts") is None
    session.close()
