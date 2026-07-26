"""A small, typed client for music artwork from the iTunes Search API."""

from importlib.metadata import PackageNotFoundError, version

from .client import Client, CoverPy, Entity
from .exceptions import (
    ArtworkUnavailableError,
    CoverPyError,
    InvalidResponseError,
    NoResultsError,
    NoResultsException,
)
from .models import Result

try:
    __version__ = version("coverpy")
except PackageNotFoundError:  # pragma: no cover - source trees are normally installed by uv
    __version__ = "0+unknown"

__all__ = [
    "ArtworkUnavailableError",
    "Client",
    "CoverPy",
    "CoverPyError",
    "Entity",
    "InvalidResponseError",
    "NoResultsError",
    "NoResultsException",
    "Result",
    "__version__",
]
