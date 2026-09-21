"""
Generates academic diagram figures for the final research paper / NTCC report.
Produces high-resolution PNGs in docs/figures/:
1. system_architecture.png
2. preprocessing_chunking_pipeline.png
3. hybrid_rerank_workflow.png
4. abstention_decision_tree.png
5. frontend_workflow.png
6. test_suite_summary.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "docs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def create_system_architecture():
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.axis("off")

    # Background containers
    offline_box = patches.FancyBboxPatch((0.02, 0.52), 0.96, 0.44, boxstyle="round,pad=0.02",
                                         facecolor="#F4F6F9", edgecolor="#2C3E50", linewidth=1.5, linestyle="--")
    online_box = patches.FancyBboxPatch((0.02, 0.04), 0.96, 0.44, boxstyle="round,pad=0.02",
                                        facecolor="#F0F7FA", edgecolor="#2980B9", linewidth=1.5, linestyle="-")
    ax.add_patch(offline_box)
    ax.add_patch(online_box)

    ax.text(0.04, 0.92, "OFFLINE: Corpus Preparation & Dual-Indexing Pipeline", fontsize=11, fontweight="bold", color="#2C3E50")
    ax.text(0.04, 0.44, "ONLINE: Evidence Retrieval, Reranking, & Grounded Generation Pipeline", fontsize=11, fontweight="bold", color="#2980B9")

    # Offline Nodes
    nodes_offline = [
        (0.05, 0.62, "Raw CTI PDFs\n(9 Reports)", "#E8F8F5", "#16A085"),
        (0.20, 0.62, "PyMuPDF Extraction\n& Text Cleaning", "#EBF5FB", "#2980B9"),
        (0.36, 0.62, "Page-Bounded Chunking\n(250 Words, 40 Overlap)", "#FEF9E7", "#F39C12"),
        (0.53, 0.62, "Metadata Binding\n(Doc, Page, Chunk ID)", "#F4ECF7", "#8E44AD"),
        (0.72, 0.76, "FAISS Dense Index\n(all-MiniLM-L6-v2, 384d)", "#FDEDEC", "#C0392B"),
        (0.72, 0.55, "BM25 Sparse Index\n(Cybersecurity Tokenizer)", "#EAECEE", "#34495E"),
    ]

    for x, y, text, fc, ec in nodes_offline:
        p = patches.FancyBboxPatch((x, y), 0.14, 0.18, boxstyle="round,pad=0.01", facecolor=fc, edgecolor=ec, linewidth=1.2)
        ax.add_patch(p)
        ax.text(x + 0.07, y + 0.09, text, ha="center", va="center", fontsize=8.5, fontweight="semibold")

    # Arrows offline
    arrows_offline = [
        ((0.19, 0.71), (0.20, 0.71)),
        ((0.34, 0.71), (0.36, 0.71)),
        ((0.50, 0.71), (0.53, 0.71)),
        ((0.67, 0.74), (0.72, 0.83)),
        ((0.67, 0.68), (0.72, 0.63)),
    ]
    for start, end in arrows_offline:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=1.5, color="#34495E"))

    # Online Nodes
    nodes_online = [
        (0.05, 0.16, "Analyst Query\n(Natural Language)", "#E8F8F5", "#16A085"),
        (0.20, 0.26, "FAISS Dense Search\n(Top-20 Semantic)", "#FDEDEC", "#C0392B"),
        (0.20, 0.08, "BM25 Keyword Search\n(Top-20 Lexical)", "#EAECEE", "#34495E"),
        (0.37, 0.16, "Reciprocal Rank Fusion\n(RRF, k=60)", "#FEF9E7", "#F39C12"),
        (0.53, 0.16, "Cross-Encoder Rerank\n(ms-marco-MiniLM-L-6-v2)", "#EBF5FB", "#2980B9"),
        (0.69, 0.26, "Grounded Generator\n(Context + [1],[2] Tags)", "#F4ECF7", "#8E44AD"),
        (0.69, 0.08, "Abstention Filter\n('Insufficient Evidence')", "#FADBD8", "#E74C3C"),
        (0.86, 0.16, "Verified Answer\n& Traceable Citations", "#D4EFDF", "#27AE60"),
    ]

    for x, y, text, fc, ec in nodes_online:
        p = patches.FancyBboxPatch((x, y), 0.13, 0.17, boxstyle="round,pad=0.01", facecolor=fc, edgecolor=ec, linewidth=1.2)
        ax.add_patch(p)
        ax.text(x + 0.065, y + 0.085, text, ha="center", va="center", fontsize=8.2, fontweight="semibold")

    # Arrows online
    arrows_online = [
        ((0.18, 0.24), (0.20, 0.32)),
        ((0.18, 0.22), (0.20, 0.16)),
        ((0.33, 0.32), (0.37, 0.26)),
        ((0.33, 0.16), (0.37, 0.22)),
        ((0.50, 0.245), (0.53, 0.245)),
        ((0.66, 0.27), (0.69, 0.32)),
        ((0.66, 0.22), (0.69, 0.16)),
        ((0.82, 0.32), (0.86, 0.26)),
        ((0.82, 0.16), (0.86, 0.23)),
    ]
    for start, end in arrows_online:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=1.5, color="#2980B9"))

    plt.tight_layout()
    p_out = FIGURES_DIR / "system_architecture.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


def create_preprocessing_pipeline():
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.axis("off")

    stages = [
        ("PDF Ingestion\n(PyMuPDF / fitz)", "#E8F8F5", "#1ABC9C"),
        ("Regex Cleaning\n(Headers, Footers, URLs)", "#EBF5FB", "#3498DB"),
        ("Page-Bounded\nChunking (250/40)", "#FEF9E7", "#F1C40F"),
        ("Metadata Binding\n(Doc, Page, Chunk ID)", "#F4ECF7", "#9B59B6"),
        ("Vector & Sparse\nDual Serialization", "#EAEDED", "#34495E"),
    ]

    for i, (title, fc, ec) in enumerate(stages):
        x = 0.05 + i * 0.19
        p = patches.FancyBboxPatch((x, 0.35), 0.15, 0.35, boxstyle="round,pad=0.02", facecolor=fc, edgecolor=ec, linewidth=1.5)
        ax.add_patch(p)
        ax.text(x + 0.075, 0.52, title, ha="center", va="center", fontsize=9, fontweight="bold")
        if i < len(stages) - 1:
            ax.annotate("", xy=(x + 0.18, 0.52), xytext=(x + 0.15, 0.52),
                        arrowprops=dict(arrowstyle="->", lw=2, color="#2C3E50"))

    ax.set_title("Threat Intelligence Document Ingestion & Chunking Pipeline", fontsize=12, fontweight="bold", pad=20)
    plt.tight_layout()
    p_out = FIGURES_DIR / "preprocessing_chunking_pipeline.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


def create_hybrid_rerank_workflow():
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.axis("off")

    # Boxes
    boxes = [
        (0.04, 0.40, 0.16, 0.25, "Analyst Query\nq", "#EAEDED", "#2C3E50"),
        (0.26, 0.60, 0.20, 0.28, "Dense Search\n(FAISS)\nRank: r_dense\nTop-20", "#FDEDEC", "#E74C3C"),
        (0.26, 0.15, 0.20, 0.28, "Sparse Search\n(BM25)\nRank: r_sparse\nTop-20", "#E8F8F5", "#1ABC9C"),
        (0.52, 0.38, 0.20, 0.30, "Reciprocal Rank\nFusion (RRF)\nscore = sum(1/(60+r))", "#FEF9E7", "#F39C12"),
        (0.78, 0.38, 0.18, 0.30, "Cross-Encoder\nReranker\n(ms-marco-MiniLM)\nTop-5 Filtered", "#EBF5FB", "#2980B9"),
    ]

    for x, y, w, h, text, fc, ec in boxes:
        p = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", facecolor=fc, edgecolor=ec, linewidth=1.5)
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, fontweight="bold")

    # Connectors
    arrows = [
        ((0.20, 0.52), (0.26, 0.72)),
        ((0.20, 0.48), (0.26, 0.28)),
        ((0.46, 0.72), (0.52, 0.56)),
        ((0.46, 0.28), (0.52, 0.48)),
        ((0.72, 0.53), (0.78, 0.53)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", lw=2, color="#34495E"))

    ax.set_title("Dual-Stage Hybrid Retrieval (RRF) and Cross-Encoder Reranking Architecture", fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    p_out = FIGURES_DIR / "hybrid_rerank_workflow.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


def create_abstention_decision_tree():
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    ax.axis("off")

    boxes = [
        (0.38, 0.82, 0.24, 0.14, "Retrieved Top Chunks\n& User Query", "#EAEDED", "#2C3E50"),
        (0.38, 0.58, 0.24, 0.16, "Condition 1:\nExplicit Technical IDs\n(CVEs/MITRE) in Query?", "#FEF9E7", "#F39C12"),
        (0.08, 0.38, 0.24, 0.16, "Condition 2:\nAre Target IDs in\nRetrieved Evidence?", "#FDEDEC", "#E74C3C"),
        (0.68, 0.38, 0.24, 0.16, "Condition 3:\nInformative Content\nWord Coverage >= 55%?", "#EBF5FB", "#2980B9"),
        (0.08, 0.08, 0.24, 0.16, "EXPLICIT ABSTENTION\n('Insufficient Evidence')", "#FADBD8", "#C0392B"),
        (0.68, 0.08, 0.24, 0.16, "GENERATE GROUNDED\nANSWER WITH [N] CITATIONS", "#D4EFDF", "#27AE60"),
    ]

    for x, y, w, h, text, fc, ec in boxes:
        p = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015", facecolor=fc, edgecolor=ec, linewidth=1.3)
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5, fontweight="bold")

    # Arrows
    ax.annotate("Input", xy=(0.50, 0.74), xytext=(0.50, 0.82), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("Yes", xy=(0.20, 0.54), xytext=(0.38, 0.64), arrowprops=dict(arrowstyle="->", lw=1.5, color="#C0392B"))
    ax.annotate("No", xy=(0.80, 0.54), xytext=(0.62, 0.64), arrowprops=dict(arrowstyle="->", lw=1.5, color="#27AE60"))
    ax.annotate("No (Missing ID)", xy=(0.20, 0.24), xytext=(0.20, 0.38), arrowprops=dict(arrowstyle="->", lw=1.5, color="#C0392B"))
    ax.annotate("Yes (IDs Found)", xy=(0.68, 0.44), xytext=(0.32, 0.44), arrowprops=dict(arrowstyle="->", lw=1.5, color="#27AE60"))
    ax.annotate("< 55% Coverage", xy=(0.32, 0.16), xytext=(0.68, 0.42), arrowprops=dict(arrowstyle="->", lw=1.5, color="#C0392B"))
    ax.annotate(">= 55% Coverage", xy=(0.80, 0.24), xytext=(0.80, 0.38), arrowprops=dict(arrowstyle="->", lw=1.5, color="#27AE60"))

    ax.set_title("Evidence Sufficiency and Anti-Hallucination Abstention Decision Tree", fontsize=11, fontweight="bold", pad=15)
    plt.tight_layout()
    p_out = FIGURES_DIR / "abstention_decision_tree.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


def create_frontend_workflow():
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.axis("off")

    steps = [
        (0.04, 0.55, "1. User Input\nSelect example or\nenter CTI question", "#E8F8F5", "#16A085"),
        (0.20, 0.55, "2. Configure Settings\nChoose Strategy (Hybrid+Rerank)\nAdjust Top-K & Threshold", "#EBF5FB", "#2980B9"),
        (0.36, 0.55, "3. Multi-Stage Retrieval\nBM25 + FAISS candidate fusion\nCross-Encoder rescoring", "#FEF9E7", "#F39C12"),
        (0.52, 0.55, "4. Evidence Gating\nCheck sufficiency threshold\nFilter ungrounded claims", "#F4ECF7", "#8E44AD"),
        (0.68, 0.70, "5A. Grounded Answer\nDisplay answer with [1],[2] tags\nShow Traceability Table", "#D4EFDF", "#27AE60"),
        (0.68, 0.30, "5B. Explicit Abstention\nShow warning banner\nRefuse unsupported answers", "#FADBD8", "#C0392B"),
        (0.85, 0.50, "6. Inspect Evidence\nExpandable raw passage\nexplorer with scores & metadata", "#EAEDED", "#2C3E50"),
    ]

    for x, y, text, fc, ec in steps:
        p = patches.FancyBboxPatch((x, y), 0.13, 0.25, boxstyle="round,pad=0.015", facecolor=fc, edgecolor=ec, linewidth=1.3)
        ax.add_patch(p)
        ax.text(x + 0.065, y + 0.125, text, ha="center", va="center", fontsize=7.8, fontweight="semibold")

    # Arrows
    ax.annotate("", xy=(0.20, 0.67), xytext=(0.17, 0.67), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.36, 0.67), xytext=(0.33, 0.67), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.52, 0.67), xytext=(0.49, 0.67), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.68, 0.78), xytext=(0.65, 0.70), arrowprops=dict(arrowstyle="->", lw=1.5, color="#27AE60"))
    ax.annotate("", xy=(0.68, 0.45), xytext=(0.65, 0.60), arrowprops=dict(arrowstyle="->", lw=1.5, color="#C0392B"))
    ax.annotate("", xy=(0.85, 0.62), xytext=(0.81, 0.78), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.85, 0.58), xytext=(0.81, 0.45), arrowprops=dict(arrowstyle="->", lw=1.5))

    ax.set_title("Streamlit Interactive Demonstration and End-to-End User Interaction Workflow", fontsize=11, fontweight="bold", pad=15)
    plt.tight_layout()
    p_out = FIGURES_DIR / "frontend_workflow.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


def create_test_suite_summary():
    fig, ax = plt.subplots(figsize=(7, 4), dpi=300)

    categories = [
        "Ingestion & Cleaning\n(tests/test_ingestion.py)",
        "Retrieval & FAISS\n(tests/test_retrieval.py)",
        "Hybrid Fusion & Rerank\n(tests/test_hybrid_and_rerank.py)",
        "RAG Pipeline & LLM\n(tests/test_rag_pipeline.py)",
        "Evaluation Metrics\n(tests/test_evaluation_metrics.py\n+ test_rag_evaluation.py)",
    ]
    test_counts = [6, 12, 5, 10, 10]
    colors = ["#1ABC9C", "#3498DB", "#F39C12", "#9B59B6", "#E74C3C"]

    bars = ax.barh(categories, test_counts, color=colors, height=0.55, edgecolor="black", linewidth=0.6)
    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"{int(w)} tests (100% Passed)", xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", ha="left", va="center", fontsize=8.5, fontweight="bold")

    ax.set_title("Distribution of 43 Passing Automated Unit & Integration Tests", fontsize=11, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Unit / Integration Tests", fontsize=9.5)
    ax.set_xlim(0, 15)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    plt.tight_layout()
    p_out = FIGURES_DIR / "test_suite_summary.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


if __name__ == "__main__":
    create_system_architecture()
    create_preprocessing_pipeline()
    create_hybrid_rerank_workflow()
    create_abstention_decision_tree()
    create_frontend_workflow()
    create_test_suite_summary()
    print("All paper diagrams successfully generated.")
