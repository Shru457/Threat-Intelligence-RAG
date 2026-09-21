# Retrieval-Augmented Generation for Threat Intelligence Report Analysis and Question Answering

## Project Overview
A research-oriented system that ingests cyber threat intelligence (CTI) reports and
allows users to ask natural-language questions, receiving grounded, citation-backed
answers generated via Retrieval-Augmented Generation (RAG).

## Problem Statement
Security analysts must manually read lengthy, unstructured threat reports to extract
key facts (IOCs, TTPs, actor attribution). This is slow and error-prone. This project
automates evidence retrieval and answer synthesis while remaining grounded in source
documents to minimize hallucination.

## Objectives
- Build a document ingestion pipeline for threat intelligence PDF reports
- Implement semantic (vector) and keyword (BM25) retrieval
- Combine both via hybrid retrieval and reranking
- Generate grounded, cited answers using an LLM
- Evaluate system quality against baseline approaches

## Planned Features
- PDF ingestion and text extraction
- Semantic search via embeddings + FAISS
- Keyword search via BM25
- Hybrid retrieval with reranking
- LLM-based grounded question answering with source citations
- Unanswerable-question detection
- Evaluation framework comparing against naive baselines

## Technology Stack
Python, FastAPI, Streamlit, PyMuPDF, Sentence-Transformers, FAISS, BM25 (rank_bm25),
LangChain (selectively), an LLM API/model, python-dotenv.

## Planned Architecture
Threat Reports → Ingestion → Extraction → Cleaning → Chunking → Embeddings →
Vector Store → Query Processing → Retrieval → Reranking → LLM → Grounded Answer
→ Source Citations

## Project Structure
See `docs/` for full structure documentation.

## Setup Instructions
1. Clone the repository
2. Create or activate a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configuration:
   Configure `.env` if using external LLM providers (e.g. `LLM_PROVIDER=gemini` or `openai`). By default, the system runs with a deterministic offline extractive provider (`LLM_PROVIDER=offline`) requiring no API keys.

## Core Commands & Execution

### 1. Run Unit & Pipeline Tests
```bash
.\.venv\Scripts\pytest.exe tests/ -v
```

### 2. Run Comprehensive Evaluation
Executes actual evaluation across all 5 configurations (BM25, Semantic, Hybrid, Hybrid+Rerank, and Final RAG Pipeline):
```bash
.\.venv\Scripts\python.exe scripts/evaluate_rag.py
```

### 3. Generate Research Artifacts & Charts
Generates publication-quality figures and Markdown summary tables:
```bash
.\.venv\Scripts\python.exe scripts/generate_all_artifacts.py
```
Outputs:
- `docs/figures/retrieval_comparison.png`
- `docs/figures/rag_quality_metrics.png`
- `docs/figures/latency_comparison.png`
- `docs/results/evaluation_table.md`
- `docs/results/sample_rag_outputs.md`

### 4. Launch Interactive Streamlit Demonstration
```bash
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

## Current Implementation Status

### IMPLEMENTED
- **Document Ingestion & Chunking**: PyMuPDF extraction, cleaning, page-bounded chunking, and structured metadata.
- **Sparse Retrieval**: BM25Okapi with cybersecurity-aware identifier preserving tokenizer (`[A-Za-z0-9._-]+`).
- **Dense Semantic Retrieval**: FAISS vector store with `all-MiniLM-L6-v2` embeddings.
- **Hybrid Retrieval**: Reciprocal Rank Fusion (RRF, $k=60$).
- **Reranking**: Cross-Encoder joint re-scoring (`ms-marco-MiniLM-L-6-v2`).
- **Phase 1 Grounded Generation**: Context construction, `[1]`, `[2]` citation mapping, identifier preservation (CVEs, MITRE IDs, hashes, IPs), and explicit abstention gating.
- **Phase 1 LLM Abstraction**: Provider-independent interface supporting Offline Extractive synthesis, Gemini, OpenAI, Groq, and Ollama.
- **Phase 2 RAG Evaluation**: 24-query ground-truth evaluation dataset covering 12 analytical categories; measured Recall@k, MRR, nDCG@5, token F1, evidence grounding (90.91%), and abstention accuracy (91.67%).
- **Phase 3 Research Artifacts**: Automated artifact generator saving result CSV/JSON, academic charts, sample citation traces, and architecture documentation.
- **Phase 4 Frontend**: Streamlit demonstration application with interactive question analysis, strategy selection, citation tracing, and raw evidence inspection.

### FUTURE WORK
- Multi-vector document representation (e.g. ColBERT late-interaction).
- Automated MITRE ATT&CK enterprise ontology graph traversal.
- Fine-tuning a domain-specific cross-encoder on CTI incident reports.
- Multi-hop agentic query decomposition for multi-document threat campaigns.