from pathlib import Path
from typing import List

from app.core.config import settings
from app.ingestion.models import DocumentChunk
from app.ingestion.parser import parse_document
from app.ingestion.qdrant_manager import QdrantManager

SUPPORTED_EXTENSIONS = {".pdf", ".md"}

VALID_COLLECTIONS = {
    "general",
    "clinical",
    "nursing",
    "billing",
    "equipment",
}


def collect_documents() -> List[tuple[Path, str]]:
    data_dir = Path(settings.DATA_DIR)
    documents = []

    for collection_dir in data_dir.iterdir():
        if not collection_dir.is_dir():
            continue

        collection = collection_dir.name

        # Important fix:
        # Do not accidentally ingest nested folders such as "mediassist_data"
        # as a collection.
        if collection not in VALID_COLLECTIONS:
            print(f"Skipping non-collection folder: {collection_dir}")
            continue

        for file_path in collection_dir.rglob("*"):
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                documents.append((file_path, collection))

    return documents


def run_ingestion():
    print("Starting MediBot ingestion...")

    documents = collect_documents()
    print(f"Found {len(documents)} documents.")

    all_chunks: List[DocumentChunk] = []

    for file_path, collection in documents:
        print(f"Parsing: {file_path.name} | collection={collection}")

        chunks = parse_document(
            file_path=file_path,
            collection=collection,
        )

        print(f"Created {len(chunks)} chunks.")
        all_chunks.extend(chunks)

    print(f"Total chunks created: {len(all_chunks)}")

    qdrant = QdrantManager()

    print("Creating Qdrant collection...")
    qdrant.recreate_collection()

    print("Uploading chunks...")
    qdrant.upsert_chunks(all_chunks)

    print("Ingestion completed successfully.")


if __name__ == "__main__":
    run_ingestion()