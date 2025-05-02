"""
Agentic RAG - A modular, production-ready Retrieval-Augmented Generation system with agentic capabilities.

This package provides a modular, production-ready Retrieval-Augmented Generation (RAG) system
with agentic capabilities for retrieving and processing information from various sources.
"""

from core import AgentType, Query, Document, AgentResult, Plan, RagOutput
from app import AgenticRag

__version__ = "1.0.0"

__all__ = [
    "AgentType",
    "Query",
    "Document",
    "AgentResult",
    "Plan",
    "RagOutput",
    "AgenticRag"
]