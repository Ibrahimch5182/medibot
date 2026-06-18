from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.routes import router as routes_router
from app.api.agent_routes import router as agent_router

app = FastAPI(
    title="MediBot API",
    description="Advanced RAG with RBAC, Hybrid Search, Reranking and SQL RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(routes_router)
app.include_router(agent_router)