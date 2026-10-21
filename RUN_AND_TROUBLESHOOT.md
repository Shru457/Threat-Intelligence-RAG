# RUN_AND_TROUBLESHOOT.md

## Overview
This guide walks you through setting up, running, and troubleshooting the **Retrieval‑Augmented Generation (RAG) Threat Intelligence** project on Windows.
It assumes you have **Python 3.11+** installed and have access to the repository at:
`c:/Users/shrut/Desktop/NTCC/Cybersecurity Threat Intelligence RAG`.

---
### 1️⃣ Prerequisites
- **Python 3.11** (the project uses compiled wheels for NumPy, Faiss‑CPU, Torch, etc.).
- **Git** (optional, for cloning the repo).
- **Ollama** server running locally (if you want to use the `ollama` LLM provider).  Pull a model, e.g.:
  ```powershell
  ollama pull llama3:8b
  ollama serve
  ```
- **VS Code** (or any IDE) for editing files.

---
### 2️⃣ Repository Clone (if not already present)
```powershell
git clone https://github.com/Shru457/Threat-Intelligence-RAG "c:/Users/shrut/Desktop/NTCC/Cybersecurity Threat Intelligence RAG"
cd "c:/Users/shrut/Desktop/NTCC/Cybersecurity Threat Intelligence RAG"
```

---
### 3️⃣ Virtual‑Environment Setup
1. **Create a fresh environment** (named `.venv2` to avoid conflicts with any old env):
   ```powershell
   py -3.11 -m venv .venv2
   ```
2. **Activate** it:
   ```powershell
   .\.venv2\Scripts\Activate.ps1   # PowerShell
   # or
   .\.venv2\Scripts\activate.bat   # CMD
   ```
3. **Upgrade pip/setuptools/wheel** (important for binary wheels):
   ```powershell
   python -m pip install --upgrade pip setuptools wheel
   ```
4. **Install project dependencies**:
   ```powershell
   python -m pip install -r requirements.txt
   ```
   - This pulls `numpy`, `faiss‑cpu`, `sentence‑transformers`, `torch`, `streamlit`, etc.
   - If you see *“Failed building wheel for numpy”* make sure you are running Python 3.11.

---
### 4️⃣ Environment Variables
1. **Copy the example** and edit with your own keys:
   ```powershell
   copy .env.example .env
   notepad .env   # edit the file
   ```
2. **Required entries** (keep the placeholder values if you only want the offline fallback):
   ```text
   LLM_API_KEY=your_key_here_placeholder
   ENVIRONMENT=development
   LLM_PROVIDER=ollama   # or "gemini", "openai", "offline"
   GEMINI_API_KEY=your_gemini_key_if_using_gemini
   ```
   The UI will display the active provider; if Ollama is not reachable it falls back to the offline extractor.

---
### 5️⃣ Running the Streamlit UI
```powershell
python -m streamlit run frontend/app.py
```
- The app will start on `http://localhost:8501`.
- If the browser does not open automatically, copy the URL into a Chrome/Edge window.
- The sidebar shows the current LLM provider – make sure it matches what you set in `.env`.

---
### 6️⃣ Sample Queries (to verify end‑to‑end functionality)
| Query | Expected behaviour |
|-------|--------------------|
| `What is CVE‑2023‑24955?` | An answer with citations, **no abstention**. |
| `What zero‑day exploit was deployed against iOS 19 in the 2029 Stuxnet reboot?` | Should **abstain** (the corpus does not contain a 2029 report), showing a warning banner. |

You can type a query in the main text box and click **🚀 Analyze Question**.
The metrics banner displays total latency, retrieval latency, citation count, and abstention status.

---
### 7️⃣ Common Errors & Fixes
| Symptom | Likely cause | Fix |
|--------|--------------|-----|
| `ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4` | PyArrow >= 20.0 was compiled against NumPy 2.0 while project uses NumPy 1.26.4. | Pin PyArrow to compatible version: `pip install pyarrow==17.0.0`. Already resolved in `requirements.txt`. |
| `ImportError: numpy.core._multiarray_umath` | Wrong Python version (e.g., 3.14) – compiled wheels unavailable. | Use the **Python 3.11** environment (`.venv2`). |
| `OSError: [WinError 1114] DLL initialization failed ... c10.dll` | PyMuPDF/fitz DLL order conflict with PyTorch on Windows. | Ensured `torch` loads first via `tests/conftest.py`. |
| `ModuleNotFoundError: sentence_transformers` | Dependencies not installed or virtual‑env not activated. | Activate `.venv2` and run `pip install -r requirements.txt`. |
| Streamlit fails to start, complaining about **Port 8501** in use. | Another process (maybe previous Streamlit) still running. | Kill the stray process (`Stop-Process -Id <pid>` in PowerShell) or change the port via `streamlit run ... --server.port 8502`. |
| LLM provider shows *fallback* despite `LLM_PROVIDER=ollama`. | Ollama server not reachable (not running or wrong address). | Verify Ollama: `ollama list` should list the model; start it with `ollama serve`. |
| No citations appear in the answer. | Retrieval index missing or corrupted. | Re‑build the index with the provided `scripts/build_index.py` script (run after activating the env). |
| UI layout looks broken (elements overlapping). | Cached UI from previous version. | Clear Streamlit cache: delete the `.streamlit` directory in the home folder or run `streamlit cache clear`.

---
### 8️⃣ Re‑building the Vector Store (optional)
If you added new PDFs or want a fresh index:
```powershell
python scripts/build_index.py
```
This will re‑populate `vectorstore/` with FAISS and BM25 indices.

---
### 9️⃣ Running the Evaluation Script
The repository ships an evaluation script that runs a set of benchmark questions:
```powershell
python scripts/evaluate_rag.py
```
It prints precision/recall metrics and saves a `evaluation_report.json` in the project root.
Make sure the virtual‑env is active before invoking the script.

---
### 🔟 Clean‑up
- Deactivate the virtual‑env: `deactivate`.
- To remove the environment completely: delete the `.venv2` folder.
- Keep `.env` out of version control – see `.gitignore`.

---
## 🎉 You’re ready!
Follow the steps above, run a couple of sample queries, and you should see a fully‑functional RAG demo with citations, latency metrics, and proper abstention handling.
If you encounter any other issue, review the **Common Errors** table or open an issue on the GitHub repo.
