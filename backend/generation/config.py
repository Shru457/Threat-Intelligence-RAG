"""
Centralized configuration for the RAG generation subsystem.
Handles LLM provider configurations, prompt templates, citation rules,
and confidence / abstention thresholds.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# --- Retrieval Defaults for Generation ---
DEFAULT_RETRIEVAL_METHOD = "hybrid_rerank"
DEFAULT_TOP_K = 5
RERANK_CANDIDATE_K = 20

# --- Confidence & Abstention Thresholds ---
# If cross-encoder relevance score of top candidate is below this,
# or if zero keyword/semantic signal exists, flag for abstention.
RERANK_ABSTENTION_THRESHOLD = -4.0  # ms-marco cross-encoder logit scale (< -4 indicates irrelevant)
SEMANTIC_ABSTENTION_THRESHOLD = 0.25 # Cosine similarity threshold for semantic retrieval
BM25_ABSTENTION_THRESHOLD = 1.0     # Minimum BM25 score

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I do not have sufficient evidence in the ingested threat intelligence reports "
    "to answer this question."
)

# --- Provider & Model Settings ---
# Options: "offline", "openai", "gemini", "ollama", "groq"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "offline").lower().strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

# API Keys (loaded strictly from environment, never hardcoded)
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Base URLs
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()

# Default external model names if none specified
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_GROQ_MODEL = "llama-3.1-70b-versatile"
DEFAULT_OLLAMA_MODEL = "llama3"

TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS = 800

# --- System Prompt ---
SYSTEM_PROMPT = """You are an expert Cyber Threat Intelligence (CTI) analyst.
Your task is to answer user questions strictly and exclusively using the provided numbered evidence passages ([1], [2], etc.).

STRICT GUIDELINES:
1. Grounding: Answer ONLY based on facts directly stated in the evidence passages. Never extrapolate, speculate, or introduce external knowledge not present in the evidence.
2. Citations: Every statement, claim, or fact in your answer MUST include one or more citations referencing the supporting evidence passage, formatted as [1], [2], etc. (e.g., "The malware maintained persistence via registry run keys [1].").
3. Technical Identifiers: Preserve exact technical identifiers such as CVE IDs (e.g., CVE-2023-24955), MITRE ATT&CK IDs (e.g., T1003.001), malware names, threat actors, file names, hashes, domain names, and IP addresses. Never alter their formatting.
4. Insufficient Evidence: If the provided evidence passages do not contain sufficient factual information to answer the question, or if no passages are relevant, you MUST respond with the exact statement:
"I do not have sufficient evidence in the ingested threat intelligence reports to answer this question."
Do not guess, apologize, or fabricate details.
"""
