"""
chunker.py — Utility to split large text into smaller, meaningful chunks
for embeddings, LLM input, or chat context windows.
"""

from typing import List

def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[str]:
    """
    Split text into overlapping chunks for better context preservation.

    Args:
        text (str): The input text to be split.
        chunk_size (int): Maximum characters per chunk.
        overlap (int): Number of characters overlapped between chunks.

    Returns:
        List[str]: List of clean text chunks.
    """
    # Clean up text — remove extra whitespace
    text = " ".join(text.split())

    # No splitting needed for small text
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Avoid cutting off words mid-way
        if end < len(text):
            next_space = text.find(" ", end)
            if next_space != -1:
                chunk = text[start:next_space]
                end = next_space

        chunks.append(chunk.strip())
        start = end - overlap  # maintain overlap between chunks

    return chunks


def estimate_num_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> int:
    """
    Estimate how many chunks will be produced from a given text.
    Useful for planning embedding or token costs.
    """
    if not text:
        return 0

    effective_size = chunk_size - overlap
    return max(1, (len(text) + effective_size - 1) // effective_size)
