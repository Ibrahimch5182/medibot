from fastapi import HTTPException

from app.core.rbac import get_accessible_collections, is_valid_role
from app.rag.hybrid_rag import hybrid_rag_chain
from app.rag.semantic_router import semantic_router
from app.rag.sql_rag import sql_rag_chain
from app.schemas.chat import ChatResponse


def process_chat(question: str, role: str) -> ChatResponse:
    """
    Central chat pipeline used by both:
    1. Normal /chat endpoint
    2. Red-Team Agent

    This keeps normal chat and agent testing consistent.
    """

    if not is_valid_role(role):
        raise HTTPException(status_code=400, detail="Invalid role")

    route_name, route_score, route_scores = semantic_router.route(question)

    print("\n" + "=" * 90)
    print("SEMANTIC ROUTER DECISION")
    print("=" * 90)
    print("Question:", question)
    print("Role:", role)
    print("Selected route:", route_name)
    print("Selected score:", route_score)
    print("All route scores:", route_scores)
    print("=" * 90)

    if route_name == "small_talk":
        return ChatResponse(
            answer=(
                "I am MediBot, a secure internal healthcare assistant for "
                "MediAssist Health Network. I can answer role-authorised "
                "document questions using Hybrid RAG and analytical database "
                "questions using SQL RAG, depending on your access level."
            ),
            sources=[],
            retrieval_type="semantic_router",
            role=role,
        )

    if route_name == "rbac_sensitive":
        return ChatResponse(
            answer=(
                f"I cannot bypass RBAC controls. As a {role}, I can only "
                f"retrieve information from your authorised collections: "
                f"{', '.join(get_accessible_collections(role))}."
            ),
            sources=[],
            retrieval_type="rbac_blocked",
            role=role,
        )

    if route_name == "claims_sql":
        if role not in ["billing_executive", "admin"]:
            return ChatResponse(
                answer=(
                    f"As a {role}, you do not have access to claims analytics. "
                    f"You can only access these document collections: "
                    f"{', '.join(get_accessible_collections(role))}."
                ),
                sources=[],
                retrieval_type="sql_rag_blocked",
                role=role,
            )

        answer = sql_rag_chain(question)

        return ChatResponse(
            answer=answer,
            sources=[],
            retrieval_type="semantic_sql_rag",
            role=role,
        )

    if route_name == "maintenance_sql":
        if role not in ["technician", "admin"]:
            return ChatResponse(
                answer=(
                    f"As a {role}, you do not have access to maintenance ticket analytics. "
                    f"You can only access these document collections: "
                    f"{', '.join(get_accessible_collections(role))}."
                ),
                sources=[],
                retrieval_type="sql_rag_blocked",
                role=role,
            )

        answer = sql_rag_chain(question)

        return ChatResponse(
            answer=answer,
            sources=[],
            retrieval_type="semantic_sql_rag",
            role=role,
        )

    result = hybrid_rag_chain(
        question=question,
        role=role,
    )

    result["retrieval_type"] = "semantic_hybrid_rag"

    return ChatResponse(**result)