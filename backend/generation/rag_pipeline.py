"""
End-to-End Grounded Threat Intelligence RAG Pipeline.

Orchestrates:
1. Retrieval & Reranking (via backend.retrieval.retriever_factory)
2. Confidence / sufficiency filtering & threshold checking
3. Context formatting with numbered evidence passages [1], [2], etc.
4. Grounded LLM generation
5. Citation extraction, validation, and metadata mapping
6. Explicit abstention handling for unanswerable/insufficient queries
7. Latency tracking and structured result packaging
"""

import time
from typing import Any

from backend.retrieval.retriever_factory import retrieve, VALID_METHODS
from .config import (
    DEFAULT_RETRIEVAL_METHOD,
    DEFAULT_TOP_K,
    INSUFFICIENT_EVIDENCE_MESSAGE,
    RERANK_ABSTENTION_THRESHOLD,
    SYSTEM_PROMPT,
)
from .context_builder import build_evidence_context, extract_citations
from .llm import BaseLLMProvider, get_llm_provider


class RAGPipeline:
    """Complete Grounded RAG Pipeline for Cyber Threat Intelligence."""

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        default_retrieval_method: str = DEFAULT_RETRIEVAL_METHOD,
        default_top_k: int = DEFAULT_TOP_K,
        abstention_threshold: float = RERANK_ABSTENTION_THRESHOLD,
    ):
        self.provider = provider or get_llm_provider()
        self.default_retrieval_method = default_retrieval_method
        self.default_top_k = default_top_k
        self.abstention_threshold = abstention_threshold

    def answer(
        self,
        query: str,
        retrieval_method: str | None = None,
        top_k: int | None = None,
        min_confidence: float | None = None,
    ) -> dict[str, Any]:
        """
        Execute full RAG flow for a threat-intelligence question.

        Returns structured dict:
            query: str
            answer: str
            is_abstention: bool
            citations: list of resolved citation dicts
            retrieved_evidence: list of retrieved chunk dicts
            retrieval_method: str
            latency_seconds: float
            provider_name: str
        """
        start_time = time.perf_counter()

        method = retrieval_method or self.default_retrieval_method
        k = top_k or self.default_top_k
        threshold = min_confidence if min_confidence is not None else self.abstention_threshold

        if method not in VALID_METHODS:
            raise ValueError(f"Invalid retrieval method '{method}'. Valid options: {VALID_METHODS}")

        # Step 1: Retrieve evidence
        retrieval_start = time.perf_counter()
        retrieved_chunks = retrieve(query, method=method, top_k=k)
        retrieval_latency = time.perf_counter() - retrieval_start

        # Step 2: Evidence sufficiency & threshold evaluation
        if not retrieved_chunks:
            total_elapsed = time.perf_counter() - start_time
            return {
                "query": query,
                "answer": INSUFFICIENT_EVIDENCE_MESSAGE,
                "is_abstention": True,
                "citations": [],
                "retrieved_evidence": [],
                "retrieval_method": method,
                "retrieval_latency_seconds": retrieval_latency,
                "latency_seconds": total_elapsed,
                "provider_name": self.provider.name,
            }

        # If using reranking, check if the best score is below the abstention threshold
        if method == "hybrid_rerank" and threshold is not None:
            top_score = retrieved_chunks[0].get("score", 0.0)
            if top_score < threshold:
                total_elapsed = time.perf_counter() - start_time
                return {
                    "query": query,
                    "answer": INSUFFICIENT_EVIDENCE_MESSAGE,
                    "is_abstention": True,
                    "citations": [],
                    "retrieved_evidence": retrieved_chunks,
                    "retrieval_method": method,
                    "retrieval_latency_seconds": retrieval_latency,
                    "latency_seconds": total_elapsed,
                    "provider_name": self.provider.name,
                }

        # Step 3: Build evidence context & citation mapping
        context_str, citation_map = build_evidence_context(retrieved_chunks)

        prompt = (
            f"Evidence Passages:\n"
            f"{context_str}\n\n"
            f"Question: {query}\n\n"
            f"Provide a grounded, factual answer citing relevant passages as [1], [2], etc. "
            f"If the evidence does not support answering this question, explicitly state: "
            f'"{INSUFFICIENT_EVIDENCE_MESSAGE}"'
        )

        # Step 4: Generate answer
        gen_start = time.perf_counter()
        try:
            raw_answer = self.provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        except Exception as err:
            logger.warning(
                f"Configured provider '{self.provider.name}' failed during generation: {err}. "
                "Falling back to OfflineExtractiveLLMProvider."
            )
            offline_fallback = OfflineExtractiveLLMProvider()
            raw_answer = offline_fallback.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        gen_latency = time.perf_counter() - gen_start

        # Step 5: Post-process abstention and citations
        norm_answer = raw_answer.strip()
        is_abstention = (
            INSUFFICIENT_EVIDENCE_MESSAGE.lower() in norm_answer.lower()
            or "insufficient evidence" in norm_answer.lower()
            or "not enough information" in norm_answer.lower()
            or "does not contain" in norm_answer.lower() and len(norm_answer) < 150
        )

        if is_abstention:
            final_answer = INSUFFICIENT_EVIDENCE_MESSAGE
            citations = []
        else:
            final_answer = norm_answer
            citations = extract_citations(final_answer, citation_map)

        total_elapsed = time.perf_counter() - start_time

        return {
            "query": query,
            "answer": final_answer,
            "is_abstention": is_abstention,
            "citations": citations,
            "retrieved_evidence": retrieved_chunks,
            "retrieval_method": method,
            "retrieval_latency_seconds": retrieval_latency,
            "generation_latency_seconds": gen_latency,
            "latency_seconds": total_elapsed,
            "provider_name": self.provider.name,
        }


def answer_threat_query(
    query: str,
    retrieval_method: str = DEFAULT_RETRIEVAL_METHOD,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """Convenience helper function to run RAG query with default pipeline."""
    pipeline = RAGPipeline()
    return pipeline.answer(query, retrieval_method=retrieval_method, top_k=top_k)
