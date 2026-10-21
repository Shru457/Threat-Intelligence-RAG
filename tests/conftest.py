"""
Pytest configuration for Cybersecurity Threat Intelligence RAG.
Pre-loads PyTorch DLLs on Windows before third-party C libraries (e.g., PyMuPDF/fitz).
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe DLL loading on Windows
try:
    import torch
except ImportError:
    pass
