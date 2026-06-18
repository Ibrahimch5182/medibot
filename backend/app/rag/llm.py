"""
LLM wrapper using Groq.

All final answer generation goes through this file.
"""

from langchain_groq import ChatGroq

from app.core.config import settings


def get_llm(temperature: float = 0.1):
    """
    Return configured Groq chat model.
    """

    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=temperature,
    )