"""Domain exceptions. Each maps to one HTTP status in main.py's exception handlers
so route handlers never need to know about status codes directly.
"""


class KnowledgeInboxError(Exception):
    """Base for all domain errors."""


class InvalidInputError(KnowledgeInboxError):
    """Caller sent something we can't act on (bad URL, empty text). -> 400."""


class ItemNotFoundError(KnowledgeInboxError):
    """Referenced item id does not exist. -> 404."""


class FetchError(KnowledgeInboxError):
    """Fetching a URL's content failed (network, non-2xx, no extractable text). -> 422."""


class ProviderError(KnowledgeInboxError):
    """Embedding or generation provider call failed (bad key, upstream down, timeout). -> 502."""
