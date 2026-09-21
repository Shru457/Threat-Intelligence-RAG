"""
Generation layer package for Threat Intelligence RAG.
Exports core generation and pipeline components.
"""

from .config import (
    DEFAULT_RETRIEVAL_METHOD,
    DEFAULT_TOP_K,
    INSUFFICIENT_EVIDENCE_MESSAGE,
    SYSTEM_PROMPT,
)
from .context_builder import (
    build_evidence_context,
    extract_citations,
    preserve_cybersecurity_identifiers,
)
from .llm import (
    BaseLLMProvider,
    OfflineExtractiveLLMProvider,
    OpenAICompatibleProvider,
    GeminiProvider,
    OllamaProvider,
    get_llm_provider,
)
from .rag_pipeline import RAGPipeline, answer_threat_query

__all__ = [
    "DEFAULT_RETRIEVAL_METHOD",
    "DEFAULT_TOP_K",
    "INSUFFICIENT_EVIDENCE_MESSAGE",
    "SYSTEM_PROMPT",
    "build_evidence_context",
    "extract_citations",
    "preserve_cybersecurity_identifiers",
    "BaseLLMProvider",
    "OfflineExtractiveLLMProvider",
    "OpenAICompatibleProvider",
    "GeminiProvider",
    "OllamaProvider",
    "get_llm_provider",
    "RAGPipeline",
    "answer_threat_query",
]
