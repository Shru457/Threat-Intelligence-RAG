# Sample Real RAG Outputs and Citation Traces

*All outputs generated from live execution of the RAG pipeline on the threat intelligence corpus.*

---

## 1. Sample Successful RAG Output (Factual / Malware Query)

- **Query**: `How many packages were infected by the ChainDrop npm worm?`
- **Category**: `factual`
- **Abstention Flag**: `False`
- **End-to-End Latency**: `1324.83 ms`

### Generated Grounded Answer:
> ChainDrop: Inside a Self-Propagating npm Worm Executive Summary Cloud credentials npm and GitHub tokens SSH keys Other sensitive developer data A self-propagating npm worm nicknamed ChainDrop infected over 400 packages that are collectively downloaded hundreds of millions of times each week [1]. Related Unit 42 Topics AI, Malware, Supply Chain, npm Packages Details of the ChainDrop npm Worm Indicators and Behavior of the ChainDrop Worm Cortex XDR and XSIAM provide behavioral detection, investigation and response that can help organizations address ChainDrop activity executing in development environments [4]. Once installed, ChainDrop steals: It can also extract temporary credentials from GitHub Actions runner memory and use stolen npm publishing tokens to infect and republish additional packages while preserving their legitimate functionality [1].

### Citation Traceability:

- **Citation `[1]`**:
  - **Document**: Unit42 Chaindrop Npm Worm 2026 (`unit42_chaindrop_npm_worm_2026`)
  - **Page Number**: 1
  - **Chunk ID**: `unit42_chaindrop_npm_worm_2026_p1_c0`
  - **Relevance Rank**: 1 (Score: 8.1005)
  - **Evidence Snippet**: *"ChainDrop: Inside a Self-Propagating npm Worm Executive Summary Cloud credentials npm and GitHub tokens SSH keys Other sensitive developer data A self-propagating npm worm nicknamed ChainDrop infected..."*

- **Citation `[4]`**:
  - **Document**: Unit42 Chaindrop Npm Worm 2026 (`unit42_chaindrop_npm_worm_2026`)
  - **Page Number**: 3
  - **Chunk ID**: `unit42_chaindrop_npm_worm_2026_p3_c0`
  - **Relevance Rank**: 4 (Score: 2.7613)
  - **Evidence Snippet**: *"Related Unit 42 Topics AI, Malware, Supply Chain, npm Packages Details of the ChainDrop npm Worm Indicators and Behavior of the ChainDrop Worm Cortex XDR and XSIAM provide behavioral detection, invest..."*

---

## 2. Sample Unanswerable Query (Explicit Abstention)

- **Query**: `What zero-day exploit was deployed against iOS 19 in the 2029 Stuxnet reboot?`
- **Category**: `unsupported_unanswerable`
- **Expected Abstention**: `True`
- **System Abstention Triggered**: `True`
- **Citation Count**: `0`

### System Response:
> **"I do not have sufficient evidence in the ingested threat intelligence reports to answer this question."**

### Abstention Analysis:
The system detected that key named entities (`iOS 19`, `2029`, `Stuxnet reboot`) had 0% coverage in the ingested 2026 threat reports. In accordance with safety and grounding guidelines, it produced the explicit abstention message and refused to fabricate an answer or phantom citations.
