"""
Chunk Audit Script for MediBot

Purpose:
This file helps us inspect how documents are currently chunked inside Qdrant.

It checks:
1. Total chunks stored
2. Chunk count by collection
3. Chunk count by source document
4. Chunk count by chunk_type
5. Average/min/max chunk length
6. Whether bad Docling object text is still present
7. Specific chunks from important files
8. Retrieval + reranking behaviour for difficult questions

Important:
Because we are using local Qdrant storage, stop FastAPI before running this.
Local Qdrant allows only one process at a time.
"""

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


from collections import Counter, defaultdict
from statistics import mean
from typing import Dict, List, Any

from qdrant_client import QdrantClient

from app.core.config import settings
from app.rag.retriever import HybridRetriever
from app.rag.reranker import CrossEncoderReranker


def load_all_qdrant_chunks() -> List[Dict[str, Any]]:
    """
    Load all stored chunks from Qdrant using scroll pagination.
    """

    client = QdrantClient(path=settings.QDRANT_PATH)

    all_chunks = []
    offset = None

    while True:
        points, next_offset = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            limit=500,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}
            all_chunks.append(payload)

        if next_offset is None:
            break

        offset = next_offset

    client.close()
    return all_chunks


def print_basic_stats(chunks: List[Dict[str, Any]]):
    """
    Print high-level chunk statistics.
    """

    print("\n" + "=" * 100)
    print("BASIC CHUNK STATS")
    print("=" * 100)

    print("Total chunks:", len(chunks))

    collections = Counter(chunk.get("collection", "UNKNOWN") for chunk in chunks)
    documents = Counter(chunk.get("source_document", "UNKNOWN") for chunk in chunks)
    chunk_types = Counter(chunk.get("chunk_type", "UNKNOWN") for chunk in chunks)

    print("\nChunks by collection:")
    for name, count in collections.most_common():
        print(f"  {name}: {count}")

    print("\nChunks by chunk_type:")
    for name, count in chunk_types.most_common():
        print(f"  {name}: {count}")

    print("\nChunks by source_document:")
    for name, count in documents.most_common():
        print(f"  {name}: {count}")

    lengths = [len(chunk.get("text", "").split()) for chunk in chunks if chunk.get("text")]

    if lengths:
        print("\nChunk word length:")
        print("  min:", min(lengths))
        print("  max:", max(lengths))
        print("  avg:", round(mean(lengths), 2))


def print_bad_text_check(chunks: List[Dict[str, Any]]):
    """
    Check whether old bad Docling object strings still exist in chunks.
    """

    print("\n" + "=" * 100)
    print("BAD TEXT CHECK")
    print("=" * 100)

    bad_markers = [
        "TextItem(",
        "TableCell(",
        "SectionHeaderItem(",
        "formatting=None",
        "ProvenanceItem(",
        "BoundingBox(",
    ]

    bad_chunks = []

    for chunk in chunks:
        text = chunk.get("text", "")
        if any(marker in text for marker in bad_markers):
            bad_chunks.append(chunk)

    print("Bad chunks found:", len(bad_chunks))

    if bad_chunks:
        print("\nSample bad chunks:")
        for chunk in bad_chunks[:5]:
            print("\n---")
            print("Document:", chunk.get("source_document"))
            print("Section:", chunk.get("section_title"))
            print("Collection:", chunk.get("collection"))
            print("Text preview:")
            print(chunk.get("text", "")[:500])


def print_section_titles(chunks: List[Dict[str, Any]]):
    """
    Print section titles by document so we can see whether parent-child structure is preserved.
    """

    print("\n" + "=" * 100)
    print("SECTION TITLES BY IMPORTANT DOCUMENT")
    print("=" * 100)

    important_docs = [
        "treatment_protocols.pdf",
        "icu_nursing_procedures.pdf",
        "equipment_manual.pdf",
        "billing_codes.pdf",
        "claim_submission_guide.md",
    ]

    for doc in important_docs:
        titles = []
        for chunk in chunks:
            if chunk.get("source_document") == doc:
                title = chunk.get("section_title", "UNKNOWN")
                if title not in titles:
                    titles.append(title)

        print("\n" + "-" * 80)
        print(doc)
        print("-" * 80)

        for title in titles[:80]:
            print(" ", title)

        if len(titles) > 80:
            print(f"  ... {len(titles) - 80} more section titles")


def print_document_chunks(
    chunks: List[Dict[str, Any]],
    source_document: str,
    keywords: List[str],
    max_chunks: int = 80,
):
    """
    Print chunks from one document, especially those matching important keywords.
    """

    print("\n" + "=" * 100)
    print(f"DOCUMENT CHUNK INSPECTION: {source_document}")
    print("=" * 100)

    doc_chunks = [
        chunk for chunk in chunks
        if chunk.get("source_document") == source_document
    ]

    print(f"Total chunks for {source_document}: {len(doc_chunks)}")

    matching_chunks = []

    for index, chunk in enumerate(doc_chunks, start=1):
        text = chunk.get("text", "")
        combined = f"{chunk.get('section_title', '')} {text}".lower()

        if any(keyword.lower() in combined for keyword in keywords):
            matching_chunks.append((index, chunk))

    print(f"Chunks matching keywords {keywords}: {len(matching_chunks)}")

    for index, chunk in matching_chunks[:max_chunks]:
        print("\n" + "-" * 80)
        print(f"Chunk number in document: {index}")
        print("Collection:", chunk.get("collection"))
        print("Chunk type:", chunk.get("chunk_type"))
        print("Section title:", chunk.get("section_title"))
        print("Access roles:", chunk.get("access_roles"))
        print("Text preview:")
        print(chunk.get("text", "")[:1200])


def run_retrieval_diagnostics():
    """
    Run difficult questions through:
    1. Hybrid retrieval top 25
    2. Cross-encoder reranking top 8

    This shows whether:
    - The right chunks are not retrieved at all, OR
    - They are retrieved but reranker drops them.
    """

    print("\n" + "=" * 100)
    print("RETRIEVAL + RERANKING DIAGNOSTICS")
    print("=" * 100)

    retriever = HybridRetriever()
    reranker = CrossEncoderReranker()

    tests = [
        {
            "role": "doctor",
            "question": (
                "For community-acquired pneumonia, what are the CURB-65 disposition rules, "
                "antimicrobial therapy regimens, monitoring requirements, and follow-up imaging requirement?"
            ),
        },
        {
            "role": "nurse",
            "question": (
                "In SOP 2 Mechanical Ventilator Management, what are the initial settings, "
                "hourly monitoring requirements, alarm responses, and VAP prevention bundle?"
            ),
        },
        {
            "role": "technician",
            "question": (
                "In section B Infusion Pump DriveFlow IP-200, what are the occlusion pressure settings, "
                "high-alert drug protocols, F-12 fault action, and maintenance schedule?"
            ),
        },
    ]

    for test in tests:
        role = test["role"]
        question = test["question"]

        print("\n" + "#" * 100)
        print("ROLE:", role)
        print("QUESTION:", question)
        print("#" * 100)

        candidates = retriever.hybrid_search(
            question=question,
            role=role,
            limit=25,
        )

        print("\nHYBRID RETRIEVAL TOP 25")
        print("-" * 100)

        for i, chunk in enumerate(candidates, start=1):
            print(f"\nCandidate {i}")
            print("Score:", chunk.get("score"))
            print("Collection:", chunk.get("collection"))
            print("Document:", chunk.get("source_document"))
            print("Section:", chunk.get("section_title"))
            print("Chunk type:", chunk.get("chunk_type"))
            print("Text preview:")
            print(chunk.get("text", "")[:500])

        reranked = reranker.rerank(
            question=question,
            chunks=candidates,
            top_k=8,
        )

        print("\nRERANKED TOP 8")
        print("-" * 100)

        for i, chunk in enumerate(reranked, start=1):
            print(f"\nReranked {i}")
            print("Rerank score:", chunk.get("rerank_score"))
            print("Collection:", chunk.get("collection"))
            print("Document:", chunk.get("source_document"))
            print("Section:", chunk.get("section_title"))
            print("Chunk type:", chunk.get("chunk_type"))
            print("Text preview:")
            print(chunk.get("text", "")[:900])


def main():
    print("\nLoading chunks from Qdrant...")
    chunks = load_all_qdrant_chunks()

    print_basic_stats(chunks)
    print_bad_text_check(chunks)
    print_section_titles(chunks)

    print_document_chunks(
        chunks=chunks,
        source_document="treatment_protocols.pdf",
        keywords=[
            "community-acquired pneumonia",
            "curb-65",
            "antimicrobial",
            "amoxicillin",
            "azithromycin",
            "piperacillin",
            "monitoring",
            "chest x-ray",
        ],
    )

    print_document_chunks(
        chunks=chunks,
        source_document="icu_nursing_procedures.pdf",
        keywords=[
            "mechanical ventilator",
            "initial settings",
            "hourly monitoring",
            "high pressure",
            "low spo",
            "vap",
            "chlorhexidine",
        ],
    )

    print_document_chunks(
        chunks=chunks,
        source_document="equipment_manual.pdf",
        keywords=[
            "DriveFlow IP-200",
            "occlusion pressure",
            "high-alert",
            "F-12",
            "drug library",
            "maintenance",
            "70% IPA",
            "battery",
        ],
    )

    run_retrieval_diagnostics()


if __name__ == "__main__":
    main()