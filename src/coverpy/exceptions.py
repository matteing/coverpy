"""Exceptions raised by coverpy."""


class CoverPyError(Exception):
    """Base class for coverpy errors."""


class NoResultsError(CoverPyError):
    """Raised when a request does not return any matching results."""


class InvalidResponseError(CoverPyError):
    """Raised when Apple returns a response that coverpy cannot parse."""


class ArtworkUnavailableError(CoverPyError):
    """Raised when a result does not include artwork."""


class MotionArtworkError(CoverPyError):
    """Raised when Apple Music motion artwork cannot be resolved."""


# Kept for users of the original 2016 API.
NoResultsException = NoResultsError
