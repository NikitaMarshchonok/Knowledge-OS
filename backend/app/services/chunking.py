from dataclasses import dataclass


@dataclass
class ChunkData:
    chunk_index: int
    content: str
    char_start: int
    char_end: int
    token_estimate: int


def estimate_tokens(text: str) -> int:
    # Lightweight approximation for planning and UI visibility.
    return max(1, len(text) // 4)


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[ChunkData]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    cleaned = text.strip()
    if not cleaned:
        return []

    chunks: list[ChunkData] = []
    start = 0
    index = 0
    length = len(cleaned)

    while start < length:
        end = min(start + chunk_size, length)
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(
                ChunkData(
                    chunk_index=index,
                    content=piece,
                    char_start=start,
                    char_end=end,
                    token_estimate=estimate_tokens(piece),
                )
            )
            index += 1

        if end >= length:
            break

        start = end - chunk_overlap

    return chunks
