"""Word-boundary sliding-window chunking.

Chosen over naive character-slicing because it never splits a word in half,
and over sentence/semantic chunking because it needs no NLP dependency and
is O(n) with predictable chunk sizes. Overlap keeps context that falls near
a chunk boundary retrievable from either neighboring chunk. See
docs/ARCHITECTURE.md for the full tradeoff discussion.
"""


def chunk_text(text: str, chunk_size_chars: int, overlap_chars: int) -> list[str]:
    if chunk_size_chars <= 0:
        raise ValueError("chunk_size_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= chunk_size_chars:
        raise ValueError("overlap_chars must be >= 0 and < chunk_size_chars")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        current.append(word)
        current_len += len(word) + 1

        if current_len >= chunk_size_chars:
            chunks.append(" ".join(current))
            current, current_len = _carry_overlap(current, overlap_chars)

    if current and " ".join(current) != (chunks[-1] if chunks else None):
        chunks.append(" ".join(current))

    return chunks


def _carry_overlap(words: list[str], overlap_chars: int) -> tuple[list[str], int]:
    """Return the trailing words of `words` covering ~overlap_chars, to seed the next chunk."""
    carried: list[str] = []
    carried_len = 0
    for word in reversed(words):
        carried_len += len(word) + 1
        carried.insert(0, word)
        if carried_len >= overlap_chars:
            break
    return carried, carried_len
