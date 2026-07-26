"""Experimental Apple Music motion artwork support."""

from __future__ import annotations

import base64
import json
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import requests

from .exceptions import MotionArtworkError

_APPLE_MUSIC_ORIGIN = "https://music.apple.com"
_AMP_API_BASE_URL = "https://amp-api.music.apple.com/v1/catalog"
_TOKEN_BOOTSTRAP_URL = f"{_APPLE_MUSIC_ORIGIN}/us/album/1693323844"
_SCRIPT_PATTERN = re.compile(r"src=[\"'](?P<path>/assets/index[^\"']+\.js)[\"']")
_TOKEN_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_ATTRIBUTE_PATTERN = re.compile(r'([A-Z0-9-]+)=(?:"([^"]*)"|([^,]*))(?:,|$)')
_MAP_URI_PATTERN = re.compile(r'URI="([^"]+)"')


@dataclass(frozen=True, slots=True)
class MotionArtwork:
    """Motion artwork URLs for an Apple Music album."""

    album_id: int
    hls_url: str
    video_url: str | None = None
    hq_video_url: str | None = None
    tall_hls_url: str | None = None

    def as_dict(self) -> dict[str, int | str | None]:
        """Return motion artwork data suitable for JSON serialization."""
        return {
            "album_id": self.album_id,
            "hls_url": self.hls_url,
            "video_url": self.video_url,
            "hq_video_url": self.hq_video_url,
            "tall_hls_url": self.tall_hls_url,
        }


@dataclass(frozen=True, slots=True)
class _HLSVariant:
    playlist_url: str
    bandwidth: int
    width: int | None
    codecs: str


class MotionArtworkResolver:
    """Resolve Apple's undocumented editorial video metadata and HLS streams."""

    def __init__(self, session: requests.Session, timeout: float) -> None:
        self._session = session
        self._timeout = timeout
        self._web_token: str | None = None
        self._web_token_expiry = 0.0

    def get(self, album_id: int, storefront: str) -> MotionArtwork | None:
        """Return motion artwork for an album when Apple provides it."""
        response = self._session.get(
            f"{_AMP_API_BASE_URL}/{storefront}/albums/{album_id}",
            params={"extend": "editorialVideo"},
            headers={
                "Authorization": f"Bearer {self._get_web_token()}",
                "Origin": _APPLE_MUSIC_ORIGIN,
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = self._json_object(response, "Apple Music returned invalid album JSON")
        data = payload.get("data")
        if not isinstance(data, list):
            raise MotionArtworkError("Apple Music response is missing album data")
        if not data:
            return None

        album = data[0]
        if not isinstance(album, Mapping):
            raise MotionArtworkError("Apple Music returned invalid album data")
        attributes = album.get("attributes")
        if not isinstance(attributes, Mapping):
            raise MotionArtworkError("Apple Music response is missing album attributes")
        editorial_video = attributes.get("editorialVideo")
        if editorial_video is None:
            return None
        if not isinstance(editorial_video, Mapping):
            raise MotionArtworkError("Apple Music returned invalid motion artwork data")

        hls_url = self._video_url(editorial_video, "motionSquareVideo1x1", "motionDetailSquare")
        if hls_url is None:
            return None
        tall_hls_url = self._video_url(editorial_video, "motionTallVideo3x4", "motionDetailTall")
        video_url, hq_video_url = self._resolve_hls(hls_url)
        return MotionArtwork(
            album_id=album_id,
            hls_url=hls_url,
            video_url=video_url,
            hq_video_url=hq_video_url,
            tall_hls_url=tall_hls_url,
        )

    def _get_web_token(self) -> str:
        if self._web_token is not None and time.time() < self._web_token_expiry - 60:
            return self._web_token

        page_response = self._session.get(_TOKEN_BOOTSTRAP_URL, timeout=self._timeout)
        page_response.raise_for_status()
        script_match = _SCRIPT_PATTERN.search(page_response.text)
        if script_match is None:
            raise MotionArtworkError("could not find the Apple Music web bundle")

        script_response = self._session.get(
            urljoin(_APPLE_MUSIC_ORIGIN, script_match.group("path")), timeout=self._timeout
        )
        script_response.raise_for_status()
        for match in _TOKEN_PATTERN.finditer(script_response.text):
            token = match.group(0)
            payload = self._decode_token_payload(token)
            if payload.get("iss") != "AMPWebPlay":
                continue
            expiry = payload.get("exp")
            self._web_token = token
            self._web_token_expiry = float(expiry) if isinstance(expiry, (int, float)) else 0.0
            return token
        raise MotionArtworkError("could not extract the Apple Music web token")

    def _resolve_hls(self, hls_url: str) -> tuple[str | None, str | None]:
        response = self._session.get(hls_url, timeout=self._timeout)
        response.raise_for_status()
        variants = self._parse_master_playlist(hls_url, response.text)
        if not variants:
            video_url = self._direct_video_url(hls_url, response.text)
            return video_url, video_url

        compatible = [variant for variant in variants if "avc1" in variant.codecs.lower()]
        candidates = compatible or variants
        standard = self._standard_variant(candidates)
        high_quality = max(candidates, key=lambda variant: (variant.width or 0, variant.bandwidth))
        video_url = self._fetch_direct_video_url(standard.playlist_url)
        if high_quality == standard:
            return video_url, video_url
        hq_video_url = self._fetch_direct_video_url(high_quality.playlist_url)
        return video_url, hq_video_url or video_url

    def _fetch_direct_video_url(self, playlist_url: str) -> str | None:
        response = self._session.get(playlist_url, timeout=self._timeout)
        response.raise_for_status()
        return self._direct_video_url(playlist_url, response.text)

    @staticmethod
    def _parse_master_playlist(hls_url: str, text: str) -> list[_HLSVariant]:
        lines = [line.strip() for line in text.splitlines()]
        variants: list[_HLSVariant] = []
        for index, line in enumerate(lines):
            if not line.startswith("#EXT-X-STREAM-INF:"):
                continue
            attributes = {
                match.group(1): match.group(2) or match.group(3)
                for match in _ATTRIBUTE_PATTERN.finditer(line.partition(":")[2])
            }
            playlist_url = next(
                (
                    candidate
                    for candidate in lines[index + 1 :]
                    if candidate and not candidate.startswith("#")
                ),
                None,
            )
            if playlist_url is None:
                continue
            resolution = attributes.get("RESOLUTION", "")
            width_text = resolution.partition("x")[0]
            width = int(width_text) if width_text.isdigit() else None
            bandwidth_text = attributes.get("AVERAGE-BANDWIDTH") or attributes.get("BANDWIDTH", "0")
            bandwidth = int(bandwidth_text) if bandwidth_text.isdigit() else 0
            variants.append(
                _HLSVariant(
                    playlist_url=urljoin(hls_url, playlist_url),
                    bandwidth=bandwidth,
                    width=width,
                    codecs=attributes.get("CODECS", ""),
                )
            )
        return variants

    @staticmethod
    def _standard_variant(variants: list[_HLSVariant]) -> _HLSVariant:
        preferred = [
            variant
            for variant in variants
            if variant.width is not None and 480 <= variant.width <= 720
        ]
        if preferred:
            return min(
                preferred,
                key=lambda variant: (abs((variant.width or 600) - 600), variant.bandwidth),
            )
        ordered = sorted(variants, key=lambda variant: variant.bandwidth)
        return ordered[len(ordered) // 3] if len(ordered) >= 3 else ordered[0]

    @staticmethod
    def _direct_video_url(playlist_url: str, text: str) -> str | None:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#EXT-X-MAP:"):
                match = _MAP_URI_PATTERN.search(stripped)
                if match is not None:
                    return str(urljoin(playlist_url, match.group(1)))
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and ".mp4" in stripped:
                return urljoin(playlist_url, stripped)
        return None

    @staticmethod
    def _video_url(editorial_video: Mapping[Any, Any], *keys: str) -> str | None:
        for key in keys:
            value = editorial_video.get(key)
            if isinstance(value, Mapping):
                video = value.get("video")
                if isinstance(video, str) and video:
                    return video
        return None

    @staticmethod
    def _decode_token_payload(token: str) -> Mapping[str, Any]:
        try:
            encoded = token.split(".")[1]
            padding = "=" * (-len(encoded) % 4)
            payload = json.loads(base64.urlsafe_b64decode(encoded + padding))
        except (IndexError, ValueError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _json_object(response: requests.Response, message: str) -> Mapping[str, Any]:
        try:
            payload: Any = response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise MotionArtworkError(message) from error
        if not isinstance(payload, Mapping):
            raise MotionArtworkError(message)
        return payload
