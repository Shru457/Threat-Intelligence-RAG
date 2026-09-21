"""
Streamlit Web Interface for Threat Intelligence RAG System.

Demonstrates:
- Query input with curated threat intelligence examples
- Configurable retrieval strategy (BM25, Semantic, Hybrid, Hybrid + Reranking)
- Top-K and abstention threshold controls
- Grounded answer synthesis with [1], [2] inline citations
- Verified citation attribution (Document title, source, page number, chunk ID)
- Clear abstention warning on unanswerable / insufficient evidence queries
- Expandable raw evidence inspector
- Latency and subsystem performance metrics
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from backend.generation.rag_pipeline import RAGPipeline
from backend.generation.config import INSUFFICIENT_EVIDENCE_MESSAGE
from backend.generation.llm import get_llm_provider

# Page Configuration
st.set_page_config(
    page_title="Threat Intelligence RAG",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Retrieval-Augmented Generation for Threat Intelligence Report Analysis and Question Answering")
st.caption("Evidence-Grounded Threat Intelligence QA with Verified Citations and Hallucination Control")

# Initialize Pipeline in session state
@st.cache_resource
def get_pipeline():
    return RAGPipeline()

pipeline = get_pipeline()

# Sidebar Configuration
st.sidebar.header("⚙️ Pipeline Configuration")

retrieval_method = st.sidebar.selectbox(
    "Retrieval Strategy",
    options=["hybrid_rerank", "hybrid", "bm25", "semantic"],
    index=0,
    format_func=lambda m: {
        "hybrid_rerank": "Hybrid + Cross-Encoder Reranking (Highest Accuracy)",
        "hybrid": "Hybrid RRF (BM25 + FAISS)",
        "bm25": "BM25 Keyword Search Only (Fastest)",
        "semantic": "Dense Semantic Search (FAISS Only)",
    }[m],
)

top_k = st.sidebar.slider("Top-K Evidence Passages", min_value=1, max_value=10, value=5, step=1)
abstention_threshold = st.sidebar.slider(
    "Relevance Abstention Threshold",
    min_value=-8.0,
    max_value=2.0,
    value=-4.0,
    step=0.5,
    help="Cross-encoder relevance threshold below which the system abstains from answering.",
)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Ingested Corpus")
st.sidebar.markdown("""
- **Corpus**: 9 CTI PDF Reports (549 Chunks)
- **Sources**: Mandiant M-Trends 2026, Palo Alto Unit 42 (ChainDrop, SPIFFE/SPIRE, Spring Ring, etc.)
- **Active LLM Provider**: `{}`
""".format(pipeline.provider.name))

# Example Questions
EXAMPLE_QUESTIONS = [
    "— Select an example question —",
    "How many packages were infected by the ChainDrop npm worm?",
    "Which threat actor claimed responsibility for the large-scale credential theft in August 2026?",
    "Which malware families query LLMs mid-execution to evade detection according to M-Trends 2026?",
    "What vulnerability is identified as CVE-2023-24955?",
    "Which MITRE ATT&CK technique is referenced for OS Credential Dumping?",
    "What communication platform was leveraged as the primary vector in the Spring Ring campaign?",
    "How can unauthorized workloads spoof trusted identity tokens in Kubernetes clusters using SPIFFE/SPIRE?",
    "What shared observation regarding voice phishing is reported by both Google Cloud and Unit 42?",
    "What zero-day exploit was deployed against iOS 19 in the 2029 Stuxnet reboot?",
]

selected_example = st.selectbox("💡 Quick-Load Threat Intelligence Examples:", options=EXAMPLE_QUESTIONS)

default_query = selected_example if selected_example != EXAMPLE_QUESTIONS[0] else ""

query_input = st.text_input(
    "Enter a Cyber Threat Intelligence Question:",
    value=default_query,
    placeholder="e.g., How did the malware maintain persistence on infected systems?",
)

col1, col2 = st.columns([1, 6])
with col1:
    search_clicked = st.button("🚀 Analyze Question", type="primary", use_container_width=True)

if search_clicked and query_input.strip():
    with st.spinner("Executing retrieval, reranking, and grounded answer synthesis..."):
        result = pipeline.answer(
            query=query_input.strip(),
            retrieval_method=retrieval_method,
            top_k=top_k,
            min_confidence=abstention_threshold,
        )

    # Metrics Banner
    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Latency", f"{result['latency_seconds']*1000:.1f} ms")
    m_col2.metric("Retrieval Latency", f"{result.get('retrieval_latency_seconds', 0)*1000:.1f} ms")
    m_col3.metric("Citations Count", len(result["citations"]))
    m_col4.metric("Abstention Status", "ABSTAINED" if result["is_abstention"] else "ANSWERED")

    # Output Display
    if result["is_abstention"]:
        st.error(f"⚠️ **EXPLICIT ABSTENTION TRIGGERED**")
        st.info(f"**System Response:**\n\n> *\"{result['answer']}\"*")
        st.caption(
            "The system abstained because the retrieved evidence did not meet the necessary "
            "factual confidence or query keyword coverage, preventing hallucination."
        )
    else:
        st.subheader("📝 Grounded Threat Intelligence Answer")
        st.markdown(f"> {result['answer']}")

        # Citations Table
        if result["citations"]:
            st.subheader("🔗 Citation Traceability")
            cite_data = []
            for c in result["citations"]:
                cite_data.append({
                    "Citation": f"[{c['citation_id']}]",
                    "Document Title": c["document_title"],
                    "Document ID": c["document_id"],
                    "Page": c["page_number"],
                    "Chunk ID": c["chunk_id"],
                    "Rank": c["rank"],
                    "Score": f"{c['score']:.4f}",
                    "Snippet": c["snippet"],
                })
            st.dataframe(cite_data, use_container_width=True)

    # Expandable Evidence Passages
    with st.expander(f"🔍 Inspect Retrieved & Ranked Evidence ({len(result['retrieved_evidence'])} Passages)", expanded=False):
        for chunk in result["retrieved_evidence"]:
            st.markdown(
                f"**Rank {chunk.get('rank', '?')}** | "
                f"**{chunk.get('document_title', 'Report')}** | "
                f"Page {chunk.get('page_number', '?')} | "
                f"Chunk ID: `{chunk.get('chunk_id', '?')}` | "
                f"Score: `{chunk.get('score', 0.0):.4f}`"
            )
            st.code(chunk.get("text", ""), language="markdown")
            st.markdown("---")
elif search_clicked:
    st.warning("Please enter a question to analyze.")
