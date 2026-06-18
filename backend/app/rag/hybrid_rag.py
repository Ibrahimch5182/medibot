"""
Hybrid RAG chain.

Flow:

question + role
 ↓
HybridRetriever with Qdrant RBAC filter
 ↓
CrossEncoder reranker
 ↓
Prompt LLM using only top reranked chunks
 ↓
Return answer + source citations
"""

from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from app.rag.llm import get_llm
from app.rag.retriever import HybridRetriever
from app.rag.reranker import CrossEncoderReranker


retriever = HybridRetriever()
reranker = CrossEncoderReranker()


def format_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Turn retrieved chunks into a readable context block for the LLM.
    """

    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Source {index}]\n"
            f"Document: {chunk['source_document']}\n"
            f"Collection: {chunk['collection']}\n"
            f"Section: {chunk['section_title']}\n"
            f"Content:\n{chunk['text']}"
        )

    return "\n\n---\n\n".join(context_parts)


def build_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Build clean source metadata for API response.
    """

    sources = []

    for chunk in chunks:
        source = {
            "source_document": chunk["source_document"],
            "section_title": chunk["section_title"],
            "collection": chunk["collection"],
        }

        if source not in sources:
            sources.append(source)

    return sources

def trim_final_chunks(chunks, max_chunks: int = 5):
    """
    Keep final context small so sources stay clean.
    We still retrieve 25 and rerank 8, but only pass the strongest 5 to the LLM.
    """
    return chunks[:max_chunks]

def hybrid_rag_chain(
    question: str,
    role: str,
) -> Dict[str, Any]:
    """
    Main Hybrid RAG function.
    """

    candidates = retriever.hybrid_search(
        question=question,
        role=role,
        limit=25,
    )

    top_chunks = reranker.rerank(
        question=question,
        chunks=candidates,
        top_k=6,
    )

    if not top_chunks:
        return {
            "answer": (
                "I could not find any relevant information in the "
                "documents available to your role."
            ),
            "sources": [],
            "retrieval_type": "hybrid_rag",
            "role": role,
        }

    context = format_context(top_chunks)

    system_prompt = """
You are MediBot, a professional internal healthcare knowledge assistant for MediAssist Health Network.

Use only the retrieved context to answer.
Do not use outside knowledge.
Do not mention "provided context", "retrieved context", or "based on the context" in the answer.

Write the answer in clean Markdown.
Use short headings and make bullet points only where necessary.
Do not add unnecessary blank lines.
Do not simply copy chunks line by line; synthesize them into a polished answer.
If the question has multiple parts, answer each part clearly.

If a requested detail is not present in the retrieved context, say:
"That detail was not found in the retrieved MediAssist documents."
Do not invent missing details.

Keep the tone professional, direct, and confident.
"""

    user_prompt = f"""
User role: {role}

Question:
{question}

Retrieved context:
{context}

Answer using only the retrieved context.
"""

    llm = get_llm()

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )

    return {
        "answer": response.content,
        "sources": build_sources(top_chunks),
        "retrieval_type": "hybrid_rag",
        "role": role,
    }