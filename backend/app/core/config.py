"""
Central configuration file.

This keeps paths, model names, and API keys in one place.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    DATA_DIR: str = os.getenv("DATA_DIR", "./data/mediassist_data")
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "./data/qdrant_storage")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "mediassist_chunks")

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    RERANKER_MODEL: str = os.getenv(
        "RERANKER_MODEL",
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
    )
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")


settings = Settings()