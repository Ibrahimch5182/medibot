from fastapi import APIRouter, HTTPException

from app.core.rbac import get_accessible_collections, is_valid_role
from app.schemas.chat import ChatRequest, ChatResponse, CollectionsResponse
from app.services.chat_service import process_chat

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "MediBot API"}


@router.get("/collections/{role}", response_model=CollectionsResponse)
def collections(role: str):
    if not is_valid_role(role):
        raise HTTPException(status_code=400, detail="Invalid role")

    return CollectionsResponse(
        role=role,
        collections=get_accessible_collections(role),
    )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return process_chat(
        question=request.question,
        role=request.role,
    )