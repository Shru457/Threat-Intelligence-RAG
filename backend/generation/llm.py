"""
Provider-Independent LLM Abstraction Layer.

Supports:
1. OfflineExtractiveLLMProvider: Deterministic, local extractive synthesis
   ensuring reproducible evaluation and testing without API costs or internet.
2. OpenAICompatibleProvider: Works with OpenAI, Groq, OpenRouter, vLLM.
3. GeminiProvider: Google Gemini API (gemini-1.5-flash / gemini-2.0-flash).
4. OllamaProvider: Local self-hosted Ollama models.
"""

import abc
import json
import logging
import os
import re
from typing import Any

import requests

from .config import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GROQ_MODEL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENAI_MODEL,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    INSUFFICIENT_EVIDENCE_MESSAGE,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_PROVIDER,
    MAX_OUTPUT_TOKENS,
    OLLAMA_BASE_URL,
    OPENAI_API_KEY,
    SYSTEM_PROMPT,
    TEMPERATURE,
)
from .context_builder import extract_cybersecurity_identifiers

logger = logging.getLogger(__name__)


class BaseLLMProvider(abc.ABC):
    """Abstract base class for all LLM providers."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_OUTPUT_TOKENS,
    ) -> str:
        """Generate a grounded response from the provided prompt."""
        pass


class OfflineExtractiveLLMProvider(BaseLLMProvider):
    """
    Deterministic, offline extractive provider.
    Synthesizes grounded answers strictly from the provided numbered evidence blocks,
    formats citations as [1], [2], preserves cybersecurity identifiers verbatim,
    and reliably abstains when evidence is insufficient or irrelevant.
    """

    @property
    def name(self) -> str:
        return "offline_extractive"

    def _parse_prompt(self, prompt: str) -> tuple[list[tuple[int, str]], str]:
        """Extract [(citation_num, block_text)] and the question from the prompt."""
        if "\nQuestion:" in prompt:
            evidence_part, query_part = prompt.split("\nQuestion:", 1)
            query = query_part.split("\n", 1)[0].strip()
        elif "Question:" in prompt:
            evidence_part, query_part = prompt.split("Question:", 1)
            query = query_part.split("\n", 1)[0].strip()
        else:
            evidence_part = prompt
            query = ""

        pattern = re.compile(
            r"\[(\d+)\]\s+Source Document:[^\n]*\nContent:\n(.*?)(?=(?:\[\d+\]\s+Source Document:)|\Z)",
            re.DOTALL,
        )
        blocks = []
        for match in pattern.finditer(evidence_part):
            cid = int(match.group(1))
            content = match.group(2).strip()
            blocks.append((cid, content))
        return blocks, query

    def generate(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_OUTPUT_TOKENS,
    ) -> str:
        blocks, query = self._parse_prompt(prompt)

        if not blocks:
            return INSUFFICIENT_EVIDENCE_MESSAGE

        # Tokenize query into informative terms (ignoring common stopwords)
        stopwords = {
            "what", "how", "why", "which", "where", "who", "when", "the", "a", "an",
            "is", "are", "was", "were", "in", "on", "at", "by", "for", "with", "about",
            "against", "between", "into", "through", "during", "before", "after",
            "above", "below", "to", "from", "up", "down", "of", "and", "or", "did",
            "does", "do", "these", "this", "that", "those", "their", "there", "it",
            "its", "can", "could", "would", "should", "used", "carried", "out",
            "described", "associated", "identified", "observed", "reported", "discussed",
            "name", "names", "sample", "samples"
        }
        query_words = set(re.findall(r"[a-zA-Z0-9._-]+", query.lower()))
        content_words = {w for w in query_words if w not in stopwords and len(w) > 2}

        # Check for technical identifiers in the query (CVEs, MITRE IDs, hashes, IPs)
        query_identifiers = extract_cybersecurity_identifiers(query)
        target_ids = set()
        for cat, items in query_identifiers.items():
            target_ids.update(item.lower() for item in items)

        all_evidence_text = " ".join(t for _, t in blocks).lower()

        # If query contains explicit technical identifiers, ALL must be in evidence
        if target_ids and not all(tid in all_evidence_text for tid in target_ids):
            return INSUFFICIENT_EVIDENCE_MESSAGE

        # Check keyword coverage across the entire retrieved evidence
        if content_words:
            matched_words = {w for w in content_words if w in all_evidence_text}
            coverage = len(matched_words) / len(content_words)
            # Require at least 55% of content words to be present in evidence
            if coverage < 0.55:
                return INSUFFICIENT_EVIDENCE_MESSAGE

        # Score and extract relevant sentences from each evidence block
        scored_sentences = []
        best_block_overlap = 0

        for cid, text in blocks:
            text_lower = text.lower()
            raw_sentences = re.split(r"(?<=[.!?])\s+", text)
            block_overlap_count = sum(1 for w in content_words if w in text_lower)
            if block_overlap_count > best_block_overlap:
                best_block_overlap = block_overlap_count

            for sent in raw_sentences:
                sent_clean = sent.strip()
                if len(sent_clean) < 25:
                    continue
                sent_lower = sent_clean.lower()

                # Sentence matching score
                match_count = sum(1 for w in content_words if w in sent_lower)
                exact_id_bonus = 5.0 if any(tid in sent_lower for tid in target_ids) else 0.0

                if match_count >= 2 or exact_id_bonus > 0 or len(content_words) <= 2:
                    score = match_count + exact_id_bonus
                    scored_sentences.append((score, cid, sent_clean))

        if not scored_sentences:
            return INSUFFICIENT_EVIDENCE_MESSAGE

        # Sort sentences by relevance
        scored_sentences.sort(key=lambda x: x[0], reverse=True)

        # Select top non-redundant sentences up to a concise length (2-4 sentences)
        selected = []
        seen_texts = set()
        for score, cid, sent in scored_sentences:
            normalized = re.sub(r"\s+", " ", sent.lower())
            if any(normalized in s or s in normalized for s in seen_texts):
                continue
            seen_texts.add(normalized)
            selected.append((cid, sent))
            if len(selected) >= 3:
                break

        if not selected:
            return INSUFFICIENT_EVIDENCE_MESSAGE

        # Assemble grounded response with inline citations [cid]
        answer_parts = []
        for cid, sent in selected:
            # Append citation if not already ending with one
            sent_str = sent.rstrip(". ")
            answer_parts.append(f"{sent_str} [{cid}].")

        return " ".join(answer_parts)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Client for OpenAI, Groq, OpenRouter, or vLLM endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or OPENAI_API_KEY or LLM_API_KEY
        self.base_url = (base_url or LLM_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.model = model or LLM_MODEL or DEFAULT_OPENAI_MODEL

    @property
    def name(self) -> str:
        return f"openai_compatible({self.model})"

    def generate(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_OUTPUT_TOKENS,
    ) -> str:
        if not self.api_key or "placeholder" in self.api_key.lower():
            raise ValueError("OpenAICompatibleProvider requires a valid API key.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as err:
            logger.warning(f"OpenAI compatible call failed: {err}. Falling back to offline extractive provider.")
            return OfflineExtractiveLLMProvider().generate(
                prompt=prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens
            )


class GeminiProvider(BaseLLMProvider):
    """Client for Google Gemini models via Google AI REST API."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or GEMINI_API_KEY or LLM_API_KEY
        self.model = model or LLM_MODEL or DEFAULT_GEMINI_MODEL

    @property
    def name(self) -> str:
        return f"gemini({self.model})"

    def generate(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_OUTPUT_TOKENS,
    ) -> str:
        if not self.api_key or "placeholder" in self.api_key.lower():
            raise ValueError("GeminiProvider requires a valid GEMINI_API_KEY or LLM_API_KEY.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return INSUFFICIENT_EVIDENCE_MESSAGE
            return candidates[0]["content"]["parts"][0]["text"].strip()
        except Exception as err:
            logger.warning(f"Gemini API call failed: {err}. Falling back to offline extractive provider.")
            return OfflineExtractiveLLMProvider().generate(
                prompt=prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens
            )


class OllamaProvider(BaseLLMProvider):
    """Client for locally running Ollama instance."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.model = model or LLM_MODEL or DEFAULT_OLLAMA_MODEL

    @property
    def name(self) -> str:
        return f"ollama({self.model})"

    def generate(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_OUTPUT_TOKENS,
    ) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            resp = requests.post(url, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"].strip()
        except Exception as err:
            logger.warning(f"Ollama generation call failed: {err}. Falling back to offline extractive provider.")
            return OfflineExtractiveLLMProvider().generate(
                prompt=prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens
            )


def get_llm_provider(provider_name: str | None = None) -> BaseLLMProvider:
    """
    Factory function to instantiate the configured LLM provider.
    Safely falls back to OfflineExtractiveLLMProvider if credentials are missing.
    """
    chosen = (provider_name or LLM_PROVIDER or "offline").lower().strip()

    if chosen in ("offline", "mock", "heuristic", "local_extractive"):
        return OfflineExtractiveLLMProvider()

    if chosen == "gemini":
        key = GEMINI_API_KEY or LLM_API_KEY
        if not key or "placeholder" in key.lower():
            logger.warning(
                "Gemini requested but GEMINI_API_KEY is not set or is placeholder. "
                "Falling back to OfflineExtractiveLLMProvider."
            )
            return OfflineExtractiveLLMProvider()
        return GeminiProvider()

    if chosen in ("openai", "groq", "openrouter"):
        key = (
            GROQ_API_KEY
            if chosen == "groq"
            else (OPENAI_API_KEY or LLM_API_KEY)
        )
        if not key or "placeholder" in key.lower():
            logger.warning(
                f"{chosen} requested but API key is missing or placeholder. "
                "Falling back to OfflineExtractiveLLMProvider."
            )
            return OfflineExtractiveLLMProvider()

        base_url = None
        model = None
        if chosen == "groq":
            base_url = "https://api.groq.com/openai/v1"
            model = LLM_MODEL or DEFAULT_GROQ_MODEL
        return OpenAICompatibleProvider(api_key=key, base_url=base_url, model=model)

    if chosen == "ollama":
        try:
            prov = OllamaProvider()
            try:
                probe = requests.get(f"{prov.base_url}/api/tags", timeout=1.0)
                if probe.status_code == 200:
                    installed_models = probe.json().get("models", [])
                    if not installed_models:
                        logger.warning(
                            f"Ollama server is running at {prov.base_url} but has no models installed "
                            "(run 'ollama pull llama3' to install). Falling back to OfflineExtractiveLLMProvider."
                        )
                        return OfflineExtractiveLLMProvider()
                    return prov
                logger.warning(
                    f"Ollama server at {prov.base_url} returned status {probe.status_code}. "
                    "Falling back to OfflineExtractiveLLMProvider."
                )
                return OfflineExtractiveLLMProvider()
            except Exception as probe_err:
                logger.warning(
                    f"Ollama server not reachable at {prov.base_url} ({probe_err}). "
                    "Falling back to OfflineExtractiveLLMProvider."
                )
                return OfflineExtractiveLLMProvider()
        except Exception as err:
            logger.warning(f"Ollama provider failed initialization: {err}. Falling back to offline.")
            return OfflineExtractiveLLMProvider()

    # Default fallback
    logger.info(f"Unrecognized or unset provider '{chosen}'. Using OfflineExtractiveLLMProvider.")
    return OfflineExtractiveLLMProvider()
