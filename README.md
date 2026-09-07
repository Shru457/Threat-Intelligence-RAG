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
2. Create a virtual environment: `python -m venv .venv`
3. Activate it and run `pip install -r requirements.txt`
4. Copy `.env` and fill in required values
5. See `docs/` for further setup as the project develops

## Current Status
### IMPLEMENTED
- Development environment and project scaffolding

### PLANNED
- Document ingestion pipeline (Day 2)
- Embeddings and vector store (Day 3)
- Hybrid retrieval (Day 4)
- Reranking (Day 5)
- LLM integration and grounded generation (Day 6)
- API + UI + evaluation (Day 7)

### FUTURE WORK
- Cybersecurity-aware / metadata-aware retrieval
- MITRE ATT&CK-informed retrieval
- Hallucination reduction techniques
- Baseline comparisons and formal evaluation metrics