from typing import List

MAX_CHUNK_SIZE = 1000


def split_text(text: str, max_size: int = MAX_CHUNK_SIZE) -> List[str]:
    words = text.split()

    chunks = []
    current = []

    current_length = 0

    for word in words:

        if current_length + len(word) > max_size:
            chunks.append(" ".join(current))
            current = []
            current_length = 0

        current.append(word)
        current_length += len(word) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks