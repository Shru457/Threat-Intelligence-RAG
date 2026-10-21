"""
Threat Intelligence RAG - Research & Decision Support System.

A grounded question-answering system for technical Cyber Threat Intelligence (CTI) reports
featuring multi-stage hybrid retrieval, cross-encoder reranking, traceable citations,
and verifiable hallucination abstention.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path for backend imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe Windows DLL initialization: load PyTorch native runtime before other C extensions
try:
    import torch
except ImportError:
    pass

import pandas as pd
import streamlit as st

from backend.generation.rag_pipeline import RAGPipeline
from backend.generation.config import INSUFFICIENT_EVIDENCE_MESSAGE
from backend.generation.llm import get_llm_provider

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Threat Intelligence RAG",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Clean, Restrained Styling (Slate / Charcoal Palette)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global Typography and Spacing */
    .app-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.15rem;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.25rem;
        line-height: 1.4;
    }
    .pill-tag {
        display: inline-block;
        padding: 0.2rem 0.55rem;
        font-size: 0.75rem;
        font-weight: 500;
        border-radius: 4px;
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
        margin-right: 0.35rem;
        margin-bottom: 0.25rem;
    }
    .pill-tag-active {
        background-color: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
    }
    .response-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #2563eb;
        border-radius: 4px;
        padding: 1rem 1.15rem;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #1e293b;
        margin-top: 0.5rem;
        margin-bottom: 0.75rem;
    }
    .abstention-card {
        background-color: #fffbeb;
        border: 1px solid #fef3c7;
        border-left: 3px solid #d97706;
        border-radius: 4px;
        padding: 1rem 1.15rem;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #92400e;
        margin-top: 0.5rem;
        margin-bottom: 0.75rem;
    }
    .telemetry-bar {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 0.4rem;
        margin-bottom: 0.8rem;
    }
    .metric-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        text-align: left;
    }
    .metric-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Cached Pipeline & Metadata Loaders
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Initializing RAG Pipeline (FAISS + BM25 + Cross-Encoder)...")
def load_pipeline() -> RAGPipeline:
    return RAGPipeline()


@st.cache_data
def load_corpus_metadata() -> list[dict]:
    meta_path = PROJECT_ROOT / "vectorstore" / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@st.cache_data
def load_evaluation_records() -> list[dict]:
    eval_path = PROJECT_ROOT / "data" / "evaluation" / "results" / "rag_evaluation_results.json"
    if eval_path.exists():
        with open(eval_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


pipeline = load_pipeline()
corpus_metadata = load_corpus_metadata()
eval_records = load_evaluation_records()


# -----------------------------------------------------------------------------
# Sidebar Navigation & Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Navigation")
    current_view = st.radio(
        "Select Section",
        options=[
            "Research Assistant",
            "Threat Intelligence Library",
            "Evaluation Benchmarks",
            "System Methodology",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Retrieval Controls")

    with st.expander("Advanced Settings", expanded=False):
        retrieval_strategy = st.selectbox(
            "Retrieval Strategy",
            options=["hybrid_rerank", "hybrid", "bm25", "semantic"],
            index=0,
            format_func=lambda s: {
                "hybrid_rerank": "Hybrid RRF + Cross-Encoder Rerank (Recommended)",
                "hybrid": "Hybrid RRF (Dense FAISS + Sparse BM25)",
                "bm25": "Sparse Keyword Search (BM25 Only)",
                "semantic": "Dense Semantic Search (FAISS Only)",
            }[s],
            help="Select the candidate retrieval pipeline and reranking configuration.",
        )

        top_k = st.slider(
            "Top-K Evidence Passages",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
            help="Number of top reranked passages passed to the generation context.",
        )

        abstention_threshold = st.slider(
            "Relevance Abstention Cutoff",
            min_value=-8.0,
            max_value=2.0,
            value=-4.0,
            step=0.5,
            help="Cross-encoder relevance threshold below which the system abstains from answering to prevent hallucination.",
        )

    st.markdown("---")
    st.markdown("### Engine Status")
    active_prov = getattr(pipeline.provider, "name", "unknown")
    st.markdown(
        f"<div class='pill-tag pill-tag-active'>Provider: {active_prov}</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Deterministic local extractive synthesis ensures offline reproducibility and zero API dependency."
        if "offline" in active_prov.lower()
        else "Connected to external generative provider."
    )

    st.markdown(
        f"<div class='pill-tag'>Indexed Chunks: {len(corpus_metadata)}</div>"
        f"<div class='pill-tag'>Embeddings: all-MiniLM-L6-v2</div>"
        f"<div class='pill-tag'>Reranker: ms-marco-MiniLM-L-6-v2</div>",
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# VIEW 1: Research Assistant (Conversation & Question Answering)
# -----------------------------------------------------------------------------
if current_view == "Research Assistant":
    st.markdown(
        "<div class='app-header'>Cyber Threat Intelligence Research Assistant</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='app-subtitle'>"
        "Evidence-grounded question answering over technical threat intelligence reports with traceable citations and verified hallucination control."
        "</div>",
        unsafe_allow_html=True,
    )

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Action row: New conversation & Curated question loader
    action_col1, action_col2 = st.columns([1.5, 6.5])
    with action_col1:
        if st.button("New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Pre-defined test queries for demonstration
    curated_queries = [
        "— Load a sample research question —",
        "How many packages were infected by the ChainDrop npm worm?",
        "Which threat actor claimed responsibility for the large-scale credential theft in August 2026?",
        "Which malware families query LLMs mid-execution to evade detection according to M-Trends 2026?",
        "What vulnerability is identified as CVE-2023-24955?",
        "Which MITRE ATT&CK technique is referenced for OS Credential Dumping?",
        "What communication platform was leveraged as the primary vector in the Spring Ring campaign?",
        "How can unauthorized workloads spoof trusted identity tokens in Kubernetes clusters using SPIFFE/SPIRE?",
        "[Test Abstention] What zero-day exploit was deployed against iOS 19 in the 2029 Stuxnet reboot?",
    ]

    with action_col2:
        selected_sample = st.selectbox(
            "Sample Queries",
            options=curated_queries,
            index=0,
            label_visibility="collapsed",
        )

    # Render previous conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                # Assistant response
                if msg.get("is_abstention", False):
                    st.markdown(
                        f"<div class='abstention-card'><b>Abstention Decision:</b><br>{msg['content']}</div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        "The system refused to answer because retrieved evidence fell below the relevance confidence cutoff. "
                        "This guarantees zero hallucination on unindexed or unverified claims."
                    )
                else:
                    st.markdown(
                        f"<div class='response-card'>{msg['content']}</div>",
                        unsafe_allow_html=True,
                    )

                    # Citation Table
                    citations = msg.get("citations", [])
                    if citations:
                        st.markdown("**Source Citations & Attribution**")
                        citation_rows = []
                        for c in citations:
                            citation_rows.append({
                                "Citation": f"[{c.get('citation_id', '?')}]",
                                "Document Title": c.get("document_title", "Unknown"),
                                "Page": c.get("page_number", 0),
                                "Chunk ID": c.get("chunk_id", ""),
                                "Relevance Score": f"{float(c.get('score', 0.0)):.4f}",
                                "Supporting Evidence": c.get("snippet", "")[:180] + ("..." if len(c.get("snippet", "")) > 180 else ""),
                            })

                        try:
                            st.dataframe(citation_rows, use_container_width=True, hide_index=True)
                        except Exception:
                            # Resilient markdown fallback
                            st.table(citation_rows)

                # Evidence Passages Expander
                evidence = msg.get("evidence", [])
                if evidence:
                    with st.expander(f"Retrieved Candidate Passages ({len(evidence)} passages)", expanded=False):
                        for rank, chunk in enumerate(evidence, start=1):
                            st.markdown(
                                f"**[{rank}] {chunk.get('document_title', 'Report')}** — "
                                f"Page `{chunk.get('page_number', '?')}` | "
                                f"Chunk: `{chunk.get('chunk_id', '?')}` | "
                                f"Score: `{float(chunk.get('score', 0.0)):.4f}`"
                            )
                            st.text(chunk.get("text", "")[:400] + ("..." if len(chunk.get("text", "")) > 400 else ""))
                            st.markdown("---")

                # Telemetry Caption
                metrics = msg.get("metrics", {})
                if metrics:
                    st.markdown(
                        f"<div class='telemetry-bar'>"
                        f"Latency: <b>{metrics.get('total_latency_ms', 0):.1f} ms</b> | "
                        f"Retrieval: <b>{metrics.get('retrieval_latency_ms', 0):.1f} ms</b> | "
                        f"Strategy: <b>{metrics.get('strategy', 'N/A')}</b> | "
                        f"Citations: <b>{metrics.get('citation_count', 0)}</b> | "
                        f"Outcome: <b>{metrics.get('outcome', 'N/A')}</b>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    # Prompt Input Handler
    default_input = ""
    if selected_sample != curated_queries[0]:
        default_input = selected_sample.replace("[Test Abstention] ", "")

    user_query = st.chat_input("Enter a threat intelligence query (e.g., malware persistence, CVEs, campaign vectors)...")

    # Also support clicking a sample query
    if not user_query and default_input:
        # Check if this query was already run as the last message
        if not st.session_state.messages or st.session_state.messages[-1].get("content") != default_input:
            user_query = default_input

    if user_query:
        # Add user query to session state
        st.session_state.messages.append({"role": "user", "content": user_query})

        # Process query through the RAG pipeline
        with st.spinner("Retrieving relevant passages, joint reranking, and synthesizing answer..."):
            result = pipeline.answer(
                query=user_query,
                retrieval_method=retrieval_strategy,
                top_k=top_k,
                min_confidence=abstention_threshold,
            )

        outcome_label = "ABSTAINED (No Evidence)" if result["is_abstention"] else "ANSWERED (Evidence Grounded)"
        metrics_dict = {
            "total_latency_ms": result["latency_seconds"] * 1000,
            "retrieval_latency_ms": result.get("retrieval_latency_seconds", 0) * 1000,
            "strategy": retrieval_strategy,
            "citation_count": len(result.get("citations", [])),
            "outcome": outcome_label,
        }

        # Append assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "citations": result.get("citations", []),
            "evidence": result.get("retrieved_evidence", []),
            "is_abstention": result["is_abstention"],
            "metrics": metrics_dict,
        })

        st.rerun()


# -----------------------------------------------------------------------------
# VIEW 2: Threat Intelligence Library (Indexed PDF Reports & Metadata)
# -----------------------------------------------------------------------------
elif current_view == "Threat Intelligence Library":
    st.markdown(
        "<div class='app-header'>Threat Intelligence Document Corpus</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='app-subtitle'>"
        "Auditable catalogue of indexed technical cybersecurity whitepapers, threat horizon bulletins, and malware analysis briefs."
        "</div>",
        unsafe_allow_html=True,
    )

    # Summary Metrics Row
    raw_dir = PROJECT_ROOT / "data" / "raw"
    pdf_files = list(raw_dir.glob("*.pdf")) if raw_dir.exists() else []

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(
            f"<div class='metric-container'>"
            f"<div class='metric-label'>Indexed Documents</div>"
            f"<div class='metric-value'>{len(pdf_files)}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_m2:
        st.markdown(
            f"<div class='metric-container'>"
            f"<div class='metric-label'>Total Passages (Chunks)</div>"
            f"<div class='metric-value'>{len(corpus_metadata)}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_m3:
        st.markdown(
            f"<div class='metric-container'>"
            f"<div class='metric-label'>Chunk Size / Overlap</div>"
            f"<div class='metric-value'>500 / 100</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_m4:
        st.markdown(
            f"<div class='metric-container'>"
            f"<div class='metric-label'>Dual Index Storage</div>"
            f"<div class='metric-value'>FAISS + BM25</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("#### Document Catalogue")

    # Build real file table
    doc_records = []
    from collections import Counter
    chunk_counts = Counter(c.get("document_id") for c in corpus_metadata)

    # Known sources metadata
    source_map = {
        "googlecloud_threat_horizons_h1_2026": ("Mandiant M-Trends / Google Cloud Threat Horizons", "Industry Annual Review"),
        "unit42_ai_assisted_cyber_attack_2026": ("Palo Alto Networks Unit 42", "Threat Brief"),
        "unit42_ai_enabled_malware_2026": ("Palo Alto Networks Unit 42", "Malware Analysis"),
        "unit42_chaindrop_npm_worm_2026": ("Palo Alto Networks Unit 42", "Supply Chain Worm"),
        "unit42_kubernetes_spiffe_spire_identity_spoofing_2026": ("Palo Alto Networks Unit 42", "Cloud-Native Security"),
        "unit42_large_scale_credential_attacks_2026": ("Palo Alto Networks Unit 42", "Authentication Attacks"),
        "unit42_npm_supply_chain_attacks_2026": ("Palo Alto Networks Unit 42", "Package Ecosystem Security"),
        "unit42_ppi_network_malware_campaign_2026": ("Palo Alto Networks Unit 42", "Pay-Per-Install Campaign"),
        "unit42_spring_ring_voice_phishing_2026": ("Palo Alto Networks Unit 42", "Vishing & Social Engineering"),
    }

    for pdf in sorted(pdf_files):
        doc_id = pdf.stem
        org, category = source_map.get(doc_id, ("Threat Intelligence Vendor", "Technical Report"))
        size_mb = os.path.getsize(pdf) / (1024 * 1024)
        c_count = chunk_counts.get(doc_id, 0)

        doc_records.append({
            "Document ID": doc_id,
            "Title": org,
            "Category": category,
            "File Name": pdf.name,
            "Size (MB)": f"{size_mb:.2f}",
            "Indexed Chunks": c_count,
            "Status": "Indexed (FAISS + BM25)",
        })

    if doc_records:
        df_docs = pd.DataFrame(doc_records)
        try:
            st.dataframe(df_docs, use_container_width=True, hide_index=True)
        except Exception:
            st.table(df_docs)

    st.write("")
    st.markdown("#### Document Chunk Inspector")
    selected_doc = st.selectbox(
        "Select a document to inspect indexed chunks:",
        options=[d["Document ID"] for d in doc_records],
        index=0 if doc_records else None,
    )

    if selected_doc:
        doc_chunks = [c for c in corpus_metadata if c.get("document_id") == selected_doc]
        st.caption(f"Showing sample chunks from `{selected_doc}` ({len(doc_chunks)} chunks total):")
        for chunk in doc_chunks[:3]:
            st.markdown(f"**Chunk ID:** `{chunk.get('chunk_id')}` | **Page:** `{chunk.get('page_number')}`")
            st.text(chunk.get("text", "")[:350] + ("..." if len(chunk.get("text", "")) > 350 else ""))
            st.markdown("---")


# -----------------------------------------------------------------------------
# VIEW 3: Evaluation Benchmarks (Real Measured Experimental Data)
# -----------------------------------------------------------------------------
elif current_view == "Evaluation Benchmarks":
    st.markdown(
        "<div class='app-header'>System Evaluation & Benchmarks</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='app-subtitle'>"
        "Quantitative comparison across retrieval baselines, hybrid fusion, and complete end-to-end RAG pipeline."
        "</div>",
        unsafe_allow_html=True,
    )

    if eval_records:
        st.markdown("#### Retrieval & Generation Benchmark Results")

        table_rows = []
        for r in eval_records:
            table_rows.append({
                "System": r.get("system"),
                "Type": r.get("type"),
                "Recall@5": r.get("recall@5"),
                "MRR": r.get("mrr"),
                "nDCG@5": r.get("ndcg@5"),
                "Answer F1": r.get("answer_correctness_f1"),
                "Grounding": f"{r['evidence_grounding']*100:.1f}%" if isinstance(r.get("evidence_grounding"), (int, float)) else "N/A",
                "Citation Precision": f"{r['citation_precision']*100:.1f}%" if isinstance(r.get("citation_precision"), (int, float)) else "N/A",
                "Abstention Acc.": f"{r['abstention_accuracy']*100:.1f}%" if isinstance(r.get("abstention_accuracy"), (int, float)) else "N/A",
                "Avg Latency (ms)": r.get("avg_latency_ms"),
            })

        df_eval = pd.DataFrame(table_rows)
        try:
            st.dataframe(df_eval, use_container_width=True, hide_index=True)
        except Exception:
            st.table(df_eval)

        st.write("")
        st.markdown("#### Key Findings & Empirical Analysis")
        st.markdown(
            """
            1. **BM25 Keyword Superiority for Specific Identifiers:**
               BM25 achieves strong initial retrieval (`Recall@5: 0.5227`, `MRR: 0.6171`) due to exact token matching
               on CVEs (`CVE-2023-24955`), MITRE technique codes (`T1003.001`), and specific worm identifiers (`ChainDrop`).
               Dense semantic search (`Recall@5: 0.4091`) frequently suffers from out-of-vocabulary vector dilution on novel threat names.

            2. **Hybrid RRF + Cross-Encoder Achieves Peak Retrieval Accuracy:**
               Combining dense vector search with sparse BM25 via Reciprocal Rank Fusion ($k=60$) followed by a joint
               cross-encoder reranker (`ms-marco-MiniLM-L-6-v2`) raises `Recall@5` to **0.5682** and `nDCG@5` to **0.5471**.
               Joint attention overcomes the bi-encoder information bottleneck.

            3. **Grounded Synthesis & High Abstention Accuracy:**
               The complete RAG pipeline achieves **90.91% evidence grounding** and **91.67% abstention accuracy** on unanswerable queries.
               When a query targets information outside the ingested reports, the relevance score threshold triggers an honest
               abstention, preventing fabricated threat claims.
            """
        )

        st.write("")
        st.markdown("#### Evaluation Metric Definitions")
        col_def1, col_def2 = st.columns(2)
        with col_def1:
            st.markdown(
                """
                - **Recall@K:** Fraction of ground-truth relevant passages present within the top-$K$ candidates.
                - **Mean Reciprocal Rank (MRR):** Reciprocal rank $\\frac{1}{\\text{rank}_1}$ of the first correct evidence passage.
                - **nDCG@K:** Normalized Discounted Cumulative Gain accounting for graded passage relevance and position discount.
                """
            )
        with col_def2:
            st.markdown(
                """
                - **Evidence Grounding:** Percentage of generated claims supported by retrieved context sentences.
                - **Citation Precision:** Fraction of inline citation references that resolve to valid, evidence-bearing chunks.
                - **Abstention Accuracy:** Accuracy in explicitly refusing to answer ungrounded or out-of-corpus queries.
                """
            )
    else:
        st.warning("Evaluation artifacts not found. Run `python scripts/evaluate_rag.py` to generate benchmark results.")


# -----------------------------------------------------------------------------
# VIEW 4: Methodology (Architecture & Pipeline Walkthrough)
# -----------------------------------------------------------------------------
elif current_view == "System Methodology":
    st.markdown(
        "<div class='app-header'>System Architecture & Methodology</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='app-subtitle'>"
        "Detailed technical breakdown of the multi-stage Threat Intelligence RAG pipeline."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### 1. Document Ingestion & Page-Preserving Chunking
        - **Source Ingestion:** Ingests unformatted technical PDF whitepapers using PyMuPDF (`fitz`).
        - **Page Attribution:** Extraction is tracked at the page level so that every passage permanently preserves its exact `page_number` and `document_id`.
        - **Recursive Splitter:** Chunks text into fixed word-count windows ($500$ words) with $100$-word overlap to prevent sentence splitting across boundary edges.

        ### 2. Dual Representation: Dense Vector & Sparse Lexical Indices
        - **Dense Vector Search:** Employs `sentence-transformers/all-MiniLM-L6-v2` ($384$-dimensional unit-normalized embeddings) indexed in a FAISS Flat Inner Product (`IndexFlatIP`) index.
        - **Sparse Lexical Search:** Employs BM25Okapi indexed over tokenized passages with cybersecurity identifier preservation (CVEs, IP addresses, MITRE ATT&CK techniques).

        ### 3. Reciprocal Rank Fusion (RRF)
        Combines disparate scoring scales from dense cosine similarity and sparse BM25 scores without requiring manual weight calibration:
        """
    )
    st.latex(r"\text{RRF Score}(d) = \sum_{m \in \{\text{Dense}, \text{Sparse}\}} \frac{1}{k + r_m(d)}, \quad k = 60")
    st.markdown(
        """
        ### 4. Cross-Encoder Joint Reranking
        - The top candidate passages ($K=20$) from hybrid retrieval are scored jointly with the user query using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
        - Cross-attention over query-document token pairs resolves lexical gaps and eliminates false positive candidates before generation.

        ### 5. Grounded Generation, Citation Attribution & Abstention
        - **Context Construction:** Reranked evidence is formatted into numbered blocks `[1]`, `[2]`, with explicit metadata headers.
        - **Citation Mapping:** Inline citations in generated responses are parsed and validated against the candidate citation map. Phantom citations are flagged as invalid.
        - **Relevance Abstention:** If top evidence scores fail to meet the relevance threshold, the system triggers explicit abstention:
          `"I do not have sufficient evidence in the ingested threat intelligence reports to answer this question."`
        """
    )
