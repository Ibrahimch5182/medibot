"""
Pydantic schemas for request and response objects.
"""

from typing import List, Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str


class ChatRequest(BaseModel):
    question: str
    role: str


class Source(BaseModel):
    source_document: str
    section_title: str
    collection: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    retrieval_type: str
    role: str


class CollectionsResponse(BaseModel):
    role: str
    collections: List[str]