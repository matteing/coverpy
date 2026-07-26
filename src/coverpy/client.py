"""HTTP client for Apple's iTunes Search API."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any, cast

import requests

from .exceptions import InvalidResponseError, NoResultsError
from .models import Result

DEFAULT_BASE_URL = "https://itunes.apple.com"
DEFAULT_USER_AGENT = "coverpy (+https://github.com/matteing/coverpy)"


class Entity(str, Enum):
    """Music entities supported by the iTunes Search API."""

    ALBUM = "album"
    SONG = "song"
    MUSIC_TRACK = "musicTrack"
    MUSIC_ARTIST = "musicArtist"
    MUSIC_VIDEO = "musicVideo"
    MIX = "mix"


class CoverPy:
    """Search the public iTunes catalog for music and artwork."""

    def __init__(
        self,
        *,
        country: str = "US",
        timeout: float = 10.0,
        base_url: str = DEFAULT_BASE_URL,
        session: requests.Session | None = None,
    ) -> None:
        self.country = self._validate_country(country)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be a positive number")
        self.timeout = float(timeout)
        self.base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._owns_session = session is None
        self._session.headers["User-Agent"] = DEFAULT_USER_AGENT

    def __enter__(self) -> CoverPy:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close resources owned by the client."""
        if self._owns_session:
            self._session.close()

    def search(
        self,
        term: str,
        limit: int = 25,
        *,
        entity: Entity | str = Entity.ALBUM,
        country: str | None = None,
        explicit: bool | None = None,
        language: str | None = None,
        attribute: str | None = None,
    ) -> list[Result]:
        """Search music in the iTunes Store and return normalized results."""
        if not isinstance(term, str) or not term.strip():
            raise ValueError("search term must not be empty")

        params: dict[str, str | int] = {
            "term": term.strip(),
            "country": self._validate_country(country or self.country),
            "media": "music",
            "entity": self._validate_entity(entity),
            "limit": self._validate_limit(limit),
        }
        if explicit is not None:
            if not isinstance(explicit, bool):
                raise TypeError("explicit must be a boolean or None")
            params["explicit"] = "Yes" if explicit else "No"
        if language is not None:
            if language not in {"en_us", "ja_jp"}:
                raise ValueError("language must be 'en_us' or 'ja_jp'")
            params["lang"] = language
        if attribute is not None:
            if not isinstance(attribute, str) or not attribute.strip():
                raise ValueError("attribute must not be empty")
            params["attribute"] = attribute.strip()

        return self._request("search", params)

    def get_cover(
        self,
        term: str,
        limit: int = 1,
        debug: bool = False,
        *,
        entity: Entity | str = Entity.ALBUM,
        country: str | None = None,
        explicit: bool | None = None,
        language: str | None = None,
        attribute: str | None = None,
    ) -> Result:
        """Return the first search result or raise :class:`NoResultsError`."""
        del debug
        results = self.search(
            term,
            limit,
            entity=entity,
            country=country,
            explicit=explicit,
            language=language,
            attribute=attribute,
        )
        if not results:
            raise NoResultsError(f"no results found for {term!r}")
        return results[0]

    def lookup(
        self,
        identifier: int | str,
        *,
        entity: Entity | str | None = None,
        limit: int | None = None,
        country: str | None = None,
    ) -> list[Result]:
        """Look up an iTunes catalog item by its numeric identifier."""
        normalized_identifier = self._validate_identifier(identifier)
        params: dict[str, str | int] = {
            "id": normalized_identifier,
            "country": self._validate_country(country or self.country),
        }
        if entity is not None:
            params["entity"] = self._validate_entity(entity)
        if limit is not None:
            params["limit"] = self._validate_limit(limit)
        return self._request("lookup", params)

    def lookup_upc(
        self,
        upc: str,
        *,
        entity: Entity | str | None = None,
        country: str | None = None,
    ) -> list[Result]:
        """Look up an album by UPC, optionally including a related entity."""
        normalized_upc = upc.strip() if isinstance(upc, str) else ""
        if not normalized_upc.isdigit():
            raise ValueError("UPC must contain only digits")
        params: dict[str, str | int] = {
            "upc": normalized_upc,
            "country": self._validate_country(country or self.country),
        }
        if entity is not None:
            params["entity"] = self._validate_entity(entity)
        return self._request("lookup", params)

    def _request(self, endpoint: str, params: Mapping[str, str | int]) -> list[Result]:
        response = self._session.get(
            f"{self.base_url}/{endpoint}", params=dict(params), timeout=self.timeout
        )
        response.raise_for_status()
        try:
            payload: Any = response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise InvalidResponseError("Apple returned invalid JSON") from error

        if not isinstance(payload, Mapping):
            raise InvalidResponseError("Apple returned a non-object response")
        items = payload.get("results")
        result_count = payload.get("resultCount")
        if not isinstance(items, list) or not isinstance(result_count, int):
            raise InvalidResponseError("Apple response is missing results metadata")

        parsed: list[Result] = []
        for item in items:
            if not isinstance(item, Mapping) or not all(isinstance(key, str) for key in item):
                raise InvalidResponseError("Apple returned an invalid result object")
            parsed.append(Result.from_api(cast(Mapping[str, Any], item), request_url=response.url))
        return parsed

    @staticmethod
    def _validate_country(country: str) -> str:
        if not isinstance(country, str) or len(country.strip()) != 2 or not country.isalpha():
            raise ValueError("country must be a two-letter ISO 3166-1 code")
        return country.upper()

    @staticmethod
    def _validate_entity(entity: Entity | str) -> str:
        try:
            return Entity(entity).value
        except (TypeError, ValueError) as error:
            values = ", ".join(item.value for item in Entity)
            raise ValueError(f"entity must be one of: {values}") from error

    @staticmethod
    def _validate_limit(limit: int) -> int:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ValueError("limit must be an integer between 1 and 200")
        return limit

    @staticmethod
    def _validate_identifier(identifier: int | str) -> str:
        if isinstance(identifier, bool):
            raise ValueError("identifier must be a positive integer")
        normalized = str(identifier).strip()
        if not normalized.isdigit() or int(normalized) <= 0:
            raise ValueError("identifier must be a positive integer")
        return normalized


Client = CoverPy
