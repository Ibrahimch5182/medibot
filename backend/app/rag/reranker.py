"""
Cross-encoder reranker.

Hybrid search gives us broad candidates.
The reranker chooses the most relevant ones.

Assignment requirement:
Do not pass all top-10 retrieved chunks to the LLM.
Only pass reranked top chunks.
"""

from typing import Any, Dict, List

from sentence_transformers import CrossEncoder

from app.core.config import settings


class CrossEncoderReranker:
    def __init__(self):
        self.model = CrossEncoder(settings.RERANKER_MODEL)

    def rerank(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Rerank retrieved chunks using query + chunk jointly.
        """

        if not chunks:
            return []

        pairs = [
            [question, chunk["text"]]
            for chunk in chunks
        ]

        scores = self.model.predict(pairs)

        reranked = []

        for chunk, score in zip(chunks, scores):
            new_chunk = dict(chunk)
            new_chunk["rerank_score"] = float(score)
            reranked.append(new_chunk)

        reranked.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )

        return reranked[:top_k]