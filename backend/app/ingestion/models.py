"""
Data models used during document ingestion.

Every chunk inserted into Qdrant will be represented using this structure.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class DocumentChunk:
    """
    Represents a single chunk stored in Qdrant.
    """

    text: str

    source_document: str

    collection: str

    access_roles: List[str]

    section_title: str

    chunk_type: str