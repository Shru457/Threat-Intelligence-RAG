"""
Generates visual figures of the Streamlit Frontend UI for inclusion in the research paper.
Produces:
1. docs/figures/ui_grounded_answer.png
2. docs/figures/ui_abstention_warning.png
3. docs/figures/ui_evidence_inspector.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "docs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def create_ui_grounded_answer():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.axis("off")
    ax.set_facecolor("#FFFFFF")

    # Main window border
    window = patches.FancyBboxPatch((0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.01",
                                   facecolor="#F8F9FA", edgecolor="#D1D5DB", linewidth=1.5)
    ax.add_patch(window)

    # Header bar
    header = patches.Rectangle((0.01, 0.88), 0.98, 0.11, facecolor="#0E1117")
    ax.add_patch(header)
    ax.text(0.04, 0.945, "Retrieval-Augmented Generation for Threat Intelligence Report Analysis",
            color="#FFFFFF", fontsize=12, fontweight="bold")
    ax.text(0.04, 0.905, "Evidence-Grounded Threat Intelligence QA with Verified Citations and Hallucination Control",
            color="#9CA3AF", fontsize=9)

    # Sidebar
    sidebar = patches.Rectangle((0.01, 0.01), 0.28, 0.87, facecolor="#F0F2F6", edgecolor="#E5E7EB")
    ax.add_patch(sidebar)
    ax.text(0.03, 0.83, "Pipeline Configuration", fontsize=10, fontweight="bold", color="#111827")
    ax.text(0.03, 0.78, "Retrieval Strategy:\n[ Hybrid + Cross-Encoder Reranking ]", fontsize=8, color="#374151")
    ax.text(0.03, 0.71, "Top-K Evidence Passages: 5", fontsize=8, color="#374151")
    ax.text(0.03, 0.65, "Abstention Threshold: -4.0", fontsize=8, color="#374151")
    ax.text(0.03, 0.57, "Ingested Corpus:\n• 9 CTI PDF Reports (549 Chunks)\n• Mandiant M-Trends 2026\n• Unit 42 Research Series\n• Active LLM: offline_extractive",
            fontsize=7.8, color="#4B5563")

    # Main Panel: Query Input
    ax.text(0.32, 0.83, "Enter a Cyber Threat Intelligence Question:", fontsize=10, fontweight="bold", color="#111827")
    q_box = patches.FancyBboxPatch((0.32, 0.75), 0.64, 0.065, boxstyle="round,pad=0.008",
                                  facecolor="#FFFFFF", edgecolor="#3B82F6", linewidth=1.2)
    ax.add_patch(q_box)
    ax.text(0.335, 0.78, "How many packages were infected by the ChainDrop npm worm?", fontsize=9, color="#111827", fontweight="semibold")

    # Latency Metrics Badges
    badges = [
        (0.32, "Total Latency", "3580.6 ms", "#EFF6FF", "#3B82F6"),
        (0.48, "Retrieval Latency", "2732.4 ms", "#F0FDF4", "#22C55E"),
        (0.64, "Citations Count", "2 Citations", "#FAF5FF", "#A855F7"),
        (0.80, "Abstention Status", "ANSWERED", "#F0FDF4", "#16A34A"),
    ]
    for bx, label, val, bg, fg in badges:
        b_patch = patches.FancyBboxPatch((bx, 0.65), 0.14, 0.075, boxstyle="round,pad=0.008", facecolor=bg, edgecolor=fg, linewidth=0.8)
        ax.add_patch(b_patch)
        ax.text(bx + 0.07, 0.695, label, fontsize=7.5, color="#6B7280", ha="center")
        ax.text(bx + 0.07, 0.665, val, fontsize=8.5, fontweight="bold", color=fg, ha="center")

    # Answer Card
    ax.text(0.32, 0.60, "Grounded Threat Intelligence Answer", fontsize=10, fontweight="bold", color="#111827")
    ans_box = patches.FancyBboxPatch((0.32, 0.42), 0.64, 0.16, boxstyle="round,pad=0.01",
                                    facecolor="#FFFFFF", edgecolor="#E5E7EB", linewidth=1.2)
    ax.add_patch(ans_box)
    ans_text = (
        "A self-propagating npm worm nicknamed ChainDrop infected over 400 packages that are collectively\n"
        "downloaded hundreds of millions of times each week [1]. Cortex XDR and XSIAM provide behavioral\n"
        "detection that can help organizations address ChainDrop activity executing in developer environments [4].\n"
        "Once installed, ChainDrop steals cloud credentials, npm tokens, GitHub tokens, and SSH keys [1]."
    )
    ax.text(0.335, 0.49, ans_text, fontsize=8.2, color="#1F2937", va="center", linespacing=1.4)

    # Citation Traceability Table Card
    ax.text(0.32, 0.38, "Citation Traceability Table", fontsize=10, fontweight="bold", color="#111827")
    t_box = patches.FancyBboxPatch((0.32, 0.05), 0.64, 0.31, boxstyle="round,pad=0.01",
                                  facecolor="#FFFFFF", edgecolor="#E5E7EB", linewidth=1.2)
    ax.add_patch(t_box)

    # Table Header
    t_hdr = patches.Rectangle((0.32, 0.31), 0.64, 0.045, facecolor="#F3F4F6")
    ax.add_patch(t_hdr)
    ax.text(0.34, 0.33, "Tag", fontsize=8, fontweight="bold", color="#374151")
    ax.text(0.40, 0.33, "Source Document", fontsize=8, fontweight="bold", color="#374151")
    ax.text(0.68, 0.33, "Page", fontsize=8, fontweight="bold", color="#374151")
    ax.text(0.74, 0.33, "Chunk ID", fontsize=8, fontweight="bold", color="#374151")
    ax.text(0.91, 0.33, "Score", fontsize=8, fontweight="bold", color="#374151")

    # Table Rows
    rows = [
        ("[1]", "Unit42 Chaindrop Npm Worm 2026", "1", "unit42_chaindrop_npm_worm_2026_p1_c0", "8.1005", 0.25),
        ("[4]", "Unit42 Chaindrop Npm Worm 2026", "3", "unit42_chaindrop_npm_worm_2026_p3_c0", "2.7613", 0.17),
    ]
    for tag, doc, page, cid, score, ry in rows:
        ax.text(0.34, ry, tag, fontsize=8, fontweight="bold", color="#2563EB")
        ax.text(0.40, ry, doc, fontsize=7.8, color="#1F2937")
        ax.text(0.69, ry, page, fontsize=7.8, color="#1F2937")
        ax.text(0.74, ry, cid, fontsize=7.2, color="#4B5563", fontfamily="monospace")
        ax.text(0.91, ry, score, fontsize=7.8, fontweight="bold", color="#059669")
        ax.plot([0.33, 0.95], [ry - 0.03, ry - 0.03], color="#F3F4F6", lw=1)

    plt.tight_layout()
    p_out = FIGURES_DIR / "ui_grounded_answer.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


def create_ui_abstention_warning():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ax.axis("off")

    window = patches.FancyBboxPatch((0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.01",
                                   facecolor="#F8F9FA", edgecolor="#D1D5DB", linewidth=1.5)
    ax.add_patch(window)

    # Header bar
    header = patches.Rectangle((0.01, 0.86), 0.98, 0.13, facecolor="#0E1117")
    ax.add_patch(header)
    ax.text(0.04, 0.93, "Retrieval-Augmented Generation for Threat Intelligence Report Analysis",
            color="#FFFFFF", fontsize=12, fontweight="bold")
    ax.text(0.04, 0.89, "Unanswerable Question Abstention & Anti-Hallucination Guardrail",
            color="#9CA3AF", fontsize=9)

    # Query Input Box
    ax.text(0.05, 0.80, "Enter a Cyber Threat Intelligence Question:", fontsize=9.5, fontweight="bold", color="#111827")
    q_box = patches.FancyBboxPatch((0.05, 0.70), 0.90, 0.08, boxstyle="round,pad=0.008",
                                  facecolor="#FFFFFF", edgecolor="#EF4444", linewidth=1.2)
    ax.add_patch(q_box)
    ax.text(0.07, 0.74, "What zero-day exploit was deployed against iOS 19 in the 2029 Stuxnet reboot?", fontsize=9, color="#111827")

    # Metrics
    m_box = patches.FancyBboxPatch((0.05, 0.58), 0.90, 0.09, boxstyle="round,pad=0.008",
                                  facecolor="#FEF2F2", edgecolor="#F87171", linewidth=1.0)
    ax.add_patch(m_box)
    ax.text(0.12, 0.63, "Latency: 2692.8 ms", fontsize=8.5, fontweight="bold", color="#B91C1C")
    ax.text(0.38, 0.63, "Citations: 0 (No Hallucination)", fontsize=8.5, fontweight="bold", color="#B91C1C")
    ax.text(0.72, 0.63, "Status: EXPLICIT ABSTENTION", fontsize=8.5, fontweight="bold", color="#DC2626")

    # Abstention Banner
    w_box = patches.FancyBboxPatch((0.05, 0.22), 0.90, 0.32, boxstyle="round,pad=0.01",
                                  facecolor="#FFFBEB", edgecolor="#F59E0B", linewidth=1.5)
    ax.add_patch(w_box)

    ax.text(0.08, 0.47, "[ALERT] EXPLICIT ABSTENTION TRIGGERED", fontsize=11, fontweight="bold", color="#B45309")
    msg = (
        'System Response:\n'
        '"I do not have sufficient evidence in the ingested threat intelligence reports to answer this question."\n\n'
        'Reason for Abstention:\n'
        '• Out-of-Scope Detection: Target entities ("iOS 19", "2029", "Stuxnet reboot") have 0% presence in the corpus.\n'
        '• Content Word Coverage: Below the minimum 55% relevance threshold.\n'
        '• Hallucination Guard: Generation was actively suppressed to prevent fabrication of unverified threat intelligence.'
    )
    ax.text(0.08, 0.34, msg, fontsize=8.5, color="#78350F", va="center", linespacing=1.4)

    plt.tight_layout()
    p_out = FIGURES_DIR / "ui_abstention_warning.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


def create_ui_evidence_inspector():
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.axis("off")

    window = patches.FancyBboxPatch((0.01, 0.01), 0.98, 0.98, boxstyle="round,pad=0.01",
                                   facecolor="#F8F9FA", edgecolor="#D1D5DB", linewidth=1.5)
    ax.add_patch(window)

    ax.text(0.04, 0.93, "Expanded Evidence Inspector (Ranked Retrieved Passages)", fontsize=11, fontweight="bold", color="#111827")
    ax.text(0.04, 0.89, "Displays top-k ranked chunks passed from hybrid retrieval and cross-encoder reranking to the context builder", fontsize=8.5, color="#6B7280")

    chunks = [
        (0.04, 0.58, "Rank 1 | Score: 8.1005 | Page: 1 | Document: Unit42 Chaindrop Npm Worm 2026",
         "Chunk ID: unit42_chaindrop_npm_worm_2026_p1_c0\n"
         "\"ChainDrop: Inside a Self-Propagating npm Worm Executive Summary Cloud credentials npm and GitHub tokens SSH keys Other sensitive developer data A self-propagating npm worm nicknamed ChainDrop infected over 400 packages that are collectively downloaded hundreds of millions of times each week...\"",
         "#EFF6FF", "#3B82F6"),
        (0.04, 0.28, "Rank 2 | Score: 4.8210 | Page: 25 | Document: Unit42 Chaindrop Npm Worm 2026",
         "Chunk ID: unit42_chaindrop_npm_worm_2026_p25_c0\n"
         "\"The worm exfiltrates credentials by packing them into encrypted HTTP POST requests to attacker-controlled C2 domains...\"",
         "#F9FAFB", "#D1D5DB"),
        (0.04, 0.04, "Rank 3 | Score: 3.1450 | Page: 6 | Document: Unit42 Chaindrop Npm Worm 2026",
         "Chunk ID: unit42_chaindrop_npm_worm_2026_p6_c0\n"
         "\"Analysis of the payload revealed preinstall hooks used to execute automated package re-publishing routines...\"",
         "#F9FAFB", "#D1D5DB"),
    ]

    for x, y, hdr, body, fc, ec in chunks:
        box = patches.FancyBboxPatch((x, y), 0.92, 0.24, boxstyle="round,pad=0.008", facecolor=fc, edgecolor=ec, linewidth=1.0)
        ax.add_patch(box)
        ax.text(x + 0.02, y + 0.195, hdr, fontsize=8.5, fontweight="bold", color="#1E3A8A" if fc == "#EFF6FF" else "#374151")
        ax.text(x + 0.02, y + 0.10, body, fontsize=7.8, color="#1F2937", va="center", linespacing=1.3)

    plt.tight_layout()
    p_out = FIGURES_DIR / "ui_evidence_inspector.png"
    plt.savefig(p_out, bbox_inches="tight")
    plt.close()
    print(f"Generated: {p_out}")


if __name__ == "__main__":
    create_ui_grounded_answer()
    create_ui_abstention_warning()
    create_ui_evidence_inspector()
    print("All UI demonstration figures successfully generated.")
