"""
Hybrid retriever with RBAC.

This file does the assignment-critical part:

1. Convert question into dense vector
2. Convert question into sparse BM25 vector
3. Query Qdrant using BOTH dense + sparse vectors
4. Apply RBAC filter inside Qdrant query
5. Return only chunks allowed for the user's role
"""

from typing import Any, Dict, List

from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    FusionQuery,
    Fusion,
    Prefetch,
    SparseVector,
)

from app.core.config import settings
from app.ingestion.qdrant_manager import (
    DENSE_VECTOR_NAME,
    SPARSE_VECTOR_NAME,
)


class HybridRetriever:
    def __init__(self):
        self.client = QdrantClient(path=settings.QDRANT_PATH)

        self.dense_model = TextEmbedding(
            model_name=settings.EMBEDDING_MODEL
        )

        self.sparse_model = SparseTextEmbedding(
            model_name="Qdrant/bm25"
        )

    def _role_filter(self, role: str) -> Filter:
        """
        Creates Qdrant RBAC filter.

        Only points where access_roles contains the user's role
        are allowed to be returned.

        This is not application-side filtering.
        This filter is sent directly to Qdrant.
        """

        return Filter(
            must=[
                FieldCondition(
                    key="access_roles",
                    match=MatchValue(value=role),
                )
            ]
        )

    def hybrid_search(
        self,
        question: str,
        role: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Perform Qdrant hybrid retrieval with dense + sparse search.

        Returns candidate chunks before reranking.
        """

        dense_vector = list(self.dense_model.embed([question]))[0]
        sparse_vector = list(self.sparse_model.embed([question]))[0]

        results = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            prefetch=[
                Prefetch(
                    query=dense_vector.tolist(),
                    using=DENSE_VECTOR_NAME,
                    limit=limit,
                    filter=self._role_filter(role),
                ),
                Prefetch(
                    query=SparseVector(
                        indices=sparse_vector.indices.tolist(),
                        values=sparse_vector.values.tolist(),
                    ),
                    using=SPARSE_VECTOR_NAME,
                    limit=limit,
                    filter=self._role_filter(role),
                ),
            ],
            query=FusionQuery(
                fusion=Fusion.RRF
            ),
            limit=limit,
            with_payload=True,
        )

        chunks = []

        for point in results.points:
            payload = point.payload or {}

            chunks.append(
                {
                    "text": payload.get("text", ""),
                    "score": point.score,
                    "source_document": payload.get("source_document", ""),
                    "collection": payload.get("collection", ""),
                    "section_title": payload.get("section_title", ""),
                    "chunk_type": payload.get("chunk_type", ""),
                }
            )

        return chunks