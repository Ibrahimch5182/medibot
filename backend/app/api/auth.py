import uuid
from fastapi import APIRouter, HTTPException

from app.core.rbac import DEMO_USERS
from app.schemas.chat import LoginRequest, LoginResponse

router = APIRouter()

# Simple in-memory session store for assignment demo.
SESSIONS = {}


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = DEMO_USERS.get(request.username)

    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = str(uuid.uuid4())

    SESSIONS[token] = {
        "username": request.username,
        "role": user["role"],
    }

    return LoginResponse(
        token=token,
        role=user["role"],
        username=request.username,
    )