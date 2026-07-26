"""Typed models for iTunes Search API results."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Any

from .exceptions import ArtworkUnavailableError

_ARTWORK_SIZE_PATTERN = re.compile(
    r"\d+x\d+(?=[a-z]*(?:-\d+)?\.[a-z0-9]+(?:[?#]|$))",
    flags=re.IGNORECASE,
)


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _optional_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class Result:
    """A normalized music result returned by Apple's iTunes Search API."""

    wrapper_type: str | None = None
    kind: str | None = None
    collection_type: str | None = None
    artist_id: int | None = None
    collection_id: int | None = None
    track_id: int | None = None
    artist_name: str | None = None
    collection_name: str | None = None
    track_name: str | None = None
    artist_view_url: str | None = None
    collection_view_url: str | None = None
    track_view_url: str | None = None
    preview_url: str | None = None
    artwork_url_30: str | None = None
    artwork_url_60: str | None = None
    artwork_url_100: str | None = None
    collection_price: float | None = None
    track_price: float | None = None
    release_date: datetime | None = None
    collection_explicitness: str | None = None
    track_explicitness: str | None = None
    disc_count: int | None = None
    disc_number: int | None = None
    track_count: int | None = None
    track_number: int | None = None
    track_time_millis: int | None = None
    country: str | None = None
    currency: str | None = None
    primary_genre_name: str | None = None
    content_advisory_rating: str | None = None
    is_streamable: bool | None = None
    copyright: str | None = None
    request_url: str | None = None
    raw: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({}), repr=False, compare=False
    )

    @classmethod
    def from_api(cls, item: Mapping[str, Any], *, request_url: str | None = None) -> Result:
        """Create a result from an iTunes Search API object."""
        return cls(
            wrapper_type=_optional_str(item.get("wrapperType")),
            kind=_optional_str(item.get("kind")),
            collection_type=_optional_str(item.get("collectionType")),
            artist_id=_optional_int(item.get("artistId")),
            collection_id=_optional_int(item.get("collectionId")),
            track_id=_optional_int(item.get("trackId")),
            artist_name=_optional_str(item.get("artistName")),
            collection_name=_optional_str(item.get("collectionName")),
            track_name=_optional_str(item.get("trackName")),
            artist_view_url=_optional_str(item.get("artistViewUrl")),
            collection_view_url=_optional_str(item.get("collectionViewUrl")),
            track_view_url=_optional_str(item.get("trackViewUrl")),
            preview_url=_optional_str(item.get("previewUrl")),
            artwork_url_30=_optional_str(item.get("artworkUrl30")),
            artwork_url_60=_optional_str(item.get("artworkUrl60")),
            artwork_url_100=_optional_str(item.get("artworkUrl100")),
            collection_price=_optional_float(item.get("collectionPrice")),
            track_price=_optional_float(item.get("trackPrice")),
            release_date=_optional_datetime(item.get("releaseDate")),
            collection_explicitness=_optional_str(item.get("collectionExplicitness")),
            track_explicitness=_optional_str(item.get("trackExplicitness")),
            disc_count=_optional_int(item.get("discCount")),
            disc_number=_optional_int(item.get("discNumber")),
            track_count=_optional_int(item.get("trackCount")),
            track_number=_optional_int(item.get("trackNumber")),
            track_time_millis=_optional_int(item.get("trackTimeMillis")),
            country=_optional_str(item.get("country")),
            currency=_optional_str(item.get("currency")),
            primary_genre_name=_optional_str(item.get("primaryGenreName")),
            content_advisory_rating=_optional_str(item.get("contentAdvisoryRating")),
            is_streamable=_optional_bool(item.get("isStreamable")),
            copyright=_optional_str(item.get("copyright")),
            request_url=request_url,
            raw=MappingProxyType(dict(item)),
        )

    @property
    def name(self) -> str:
        """Return the track, collection, or artist name."""
        return self.track_name or self.collection_name or self.artist_name or "unknown"

    @property
    def type(self) -> str:
        """Return a normalized legacy result type."""
        if self.kind:
            return self.kind.lower()
        if self.collection_type and self.collection_type.lower() == "album":
            return "album"
        if self.wrapper_type:
            wrapper_type = self.wrapper_type.lower()
            if wrapper_type == "track":
                return "song"
            if wrapper_type == "collection":
                return "album"
            if wrapper_type == "artist":
                return "artist"
        return "unknown"

    @property
    def identifier(self) -> int | None:
        """Return the most specific catalog identifier available."""
        return self.track_id or self.collection_id or self.artist_id

    @property
    def store_url(self) -> str | None:
        """Return the most specific iTunes Store URL available."""
        return self.track_view_url or self.collection_view_url or self.artist_view_url

    @property
    def artwork_url(self) -> str | None:
        """Return the largest artwork URL supplied by the API."""
        return self.artwork_url_100 or self.artwork_url_60 or self.artwork_url_30

    @property
    def duration(self) -> timedelta | None:
        """Return the track duration when the result contains one."""
        if self.track_time_millis is None:
            return None
        return timedelta(milliseconds=self.track_time_millis)

    @property
    def explicitness(self) -> str | None:
        """Return track-level explicitness, falling back to collection-level data."""
        return self.track_explicitness or self.collection_explicitness

    def artwork(self, size: int = 625) -> str:
        """Return an artwork URL resized to a square of ``size`` pixels."""
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise ValueError("artwork size must be a positive integer")

        url = self.artwork_url
        if url is None:
            raise ArtworkUnavailableError(f"{self.name!r} does not include artwork")

        if "{w}" in url or "{h}" in url:
            return url.replace("{w}", str(size)).replace("{h}", str(size))
        return _ARTWORK_SIZE_PATTERN.sub(f"{size}x{size}", url, count=1)

    def as_dict(self) -> dict[str, Any]:
        """Return normalized result data suitable for JSON serialization."""
        return {
            "id": self.identifier,
            "type": self.type,
            "name": self.name,
            "artist": self.artist_name,
            "album": self.collection_name,
            "store_url": self.store_url,
            "preview_url": self.preview_url,
            "artwork_url": self.artwork_url,
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "genre": self.primary_genre_name,
            "explicitness": self.explicitness,
            "duration_ms": self.track_time_millis,
            "track_number": self.track_number,
            "track_count": self.track_count,
            "disc_number": self.disc_number,
            "disc_count": self.disc_count,
            "collection_price": self.collection_price,
            "track_price": self.track_price,
            "currency": self.currency,
            "country": self.country,
            "is_streamable": self.is_streamable,
            "copyright": self.copyright,
        }

    # Compatibility properties from coverpy 0.0.x.
    @property
    def artist(self) -> str:
        return self.artist_name or "unknown"

    @property
    def album(self) -> str:
        return self.collection_name or "unknown"

    @property
    def url(self) -> str:
        return self.request_url or ""

    @property
    def artworkThumb(self) -> str:
        return self.artwork_url or ""
