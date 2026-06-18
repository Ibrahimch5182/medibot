"""
Qdrant manager.

This file handles:
1. Creating the Qdrant collection
2. Creating dense and sparse vectors
3. Inserting chunks with metadata

Important assignment requirement:
Hybrid search means dense + sparse vectors are stored in Qdrant.
RBAC metadata is also stored in Qdrant payload.
"""

from typing import List
from uuid import uuid4

from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from app.core.config import settings
from app.ingestion.models import DocumentChunk


DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(path=settings.QDRANT_PATH)

        self.dense_model = TextEmbedding(
            model_name=settings.EMBEDDING_MODEL
        )

        self.sparse_model = SparseTextEmbedding(
            model_name="Qdrant/bm25"
        )

    def recreate_collection(self):
        """
        Recreate Qdrant collection from scratch.

        We use this during ingestion so old duplicate chunks are removed.
        """

        sample_vector = list(self.dense_model.embed(["sample text"]))[0]
        dense_size = len(sample_vector)

        if self.client.collection_exists(settings.QDRANT_COLLECTION):
            self.client.delete_collection(settings.QDRANT_COLLECTION)

        self.client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config={
                DENSE_VECTOR_NAME: VectorParams(
                    size=dense_size,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                SPARSE_VECTOR_NAME: SparseVectorParams()
            },
        )

    def upsert_chunks(self, chunks: List[DocumentChunk]):
        """
        Insert document chunks into Qdrant.
        """

        if not chunks:
            print("No chunks received for upsert.")
            return

        texts = [chunk.text for chunk in chunks]

        dense_vectors = list(self.dense_model.embed(texts))
        sparse_vectors = list(self.sparse_model.embed(texts))

        points = []

        for chunk, dense_vector, sparse_vector in zip(
            chunks,
            dense_vectors,
            sparse_vectors,
        ):
            payload = {
                "text": chunk.text,
                "source_document": chunk.source_document,
                "collection": chunk.collection,
                "access_roles": chunk.access_roles,
                "section_title": chunk.section_title,
                "chunk_type": chunk.chunk_type,
            }

            point = PointStruct(
                id=str(uuid4()),
                vector={
                    DENSE_VECTOR_NAME: dense_vector.tolist(),
                    SPARSE_VECTOR_NAME: SparseVector(
                        indices=sparse_vector.indices.tolist(),
                        values=sparse_vector.values.tolist(),
                    ),
                },
                payload=payload,
            )

            points.append(point)

        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points,
        )

        print(f"Inserted {len(points)} chunks into Qdrant.")