import re
from pathlib import Path
from typing import List, Optional

from docling.document_converter import DocumentConverter

from app.core.rbac import get_access_roles_for_collection
from app.ingestion.chunker import split_text
from app.ingestion.models import DocumentChunk


converter = DocumentConverter()


def clean_text(text: str) -> str:
    if not text:
        return ""

    replacements = {
        "Γéé": "₂",
        "ΓëÑ": "≥",
        "┬░": "°",
        "┬▒": "±",
        "┬╖": "·",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_item_text(doc_item) -> str:
    if hasattr(doc_item, "export_to_markdown"):
        try:
            markdown = doc_item.export_to_markdown()
            if markdown and markdown.strip():
                return clean_text(markdown)
        except Exception:
            pass

    text = getattr(doc_item, "text", "")
    return clean_text(str(text or ""))


def get_item_type(doc_item) -> str:
    class_name = doc_item.__class__.__name__.lower()
    label = str(getattr(doc_item, "label", "")).lower()

    if "section_header" in label or "heading" in class_name:
        return "heading"

    if "table" in label or "table" in class_name:
        return "table"

    if "code" in label or "code" in class_name:
        return "code"

    return "text"


def is_major_heading(text: str) -> bool:
    patterns = [
        r"^[A-Z]\.\s+",          # C. Community-Acquired Pneumonia
        r"^\d+\.\s+",            # 1. Cashless Claim Process
        r"^SOP\s+\d+",           # SOP 2 Mechanical Ventilator Management
        r"^[A-Z]\s*[-–]\s*",     # A - something
    ]

    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def is_document_title(text: str) -> bool:
    lowered = text.lower()

    title_words = [
        "manual",
        "protocols",
        "reference",
        "formulary",
        "policy",
        "handbook",
        "guide",
    ]

    return any(word in lowered for word in title_words) and len(text.split()) <= 10


def build_section_path(
    document_title: Optional[str],
    major_heading: Optional[str],
    minor_heading: Optional[str],
) -> str:
    parts = []

    if document_title:
        parts.append(document_title)

    if major_heading:
        parts.append(major_heading)

    if minor_heading:
        parts.append(minor_heading)

    return " > ".join(parts) if parts else "General"


def flush_buffer(
    chunks: List[DocumentChunk],
    buffer_lines: List[str],
    file_path: Path,
    collection: str,
    section_path: str,
    chunk_type: str,
):
    if not buffer_lines:
        return

    body = "\n".join(line for line in buffer_lines if line.strip()).strip()

    if not body:
        return

    enriched_text = (
        f"Document: {file_path.name}\n"
        f"Collection: {collection}\n"
        f"Section path: {section_path}\n\n"
        f"{body}"
    )

    for chunk_text in split_text(enriched_text):
        chunks.append(
            DocumentChunk(
                text=chunk_text,
                source_document=file_path.name,
                collection=collection,
                access_roles=get_access_roles_for_collection(collection),
                section_title=section_path,
                chunk_type=chunk_type,
            )
        )


def parse_document(file_path: Path, collection: str) -> List[DocumentChunk]:
    result = converter.convert(str(file_path))
    document = result.document

    chunks: List[DocumentChunk] = []

    document_title: Optional[str] = None
    major_heading: Optional[str] = None
    minor_heading: Optional[str] = None

    current_section_path = "General"
    current_chunk_type = "text"
    buffer_lines: List[str] = []

    for raw_item in document.iterate_items():
        if isinstance(raw_item, tuple):
            doc_item = raw_item[0]
        else:
            doc_item = raw_item

        item_text = get_item_text(doc_item)
        item_type = get_item_type(doc_item)

        if not item_text:
            continue

        if item_type == "heading":
            flush_buffer(
                chunks=chunks,
                buffer_lines=buffer_lines,
                file_path=file_path,
                collection=collection,
                section_path=current_section_path,
                chunk_type=current_chunk_type,
            )

            buffer_lines = []
            current_chunk_type = "text"

            if document_title is None and is_document_title(item_text):
                document_title = item_text
            elif is_major_heading(item_text):
                major_heading = item_text
                minor_heading = None
            else:
                minor_heading = item_text

            current_section_path = build_section_path(
                document_title=document_title,
                major_heading=major_heading,
                minor_heading=minor_heading,
            )

            continue

        if item_type == "table":
            current_chunk_type = "table"

        buffer_lines.append(item_text)

    flush_buffer(
        chunks=chunks,
        buffer_lines=buffer_lines,
        file_path=file_path,
        collection=collection,
        section_path=current_section_path,
        chunk_type=current_chunk_type,
    )

    return chunks