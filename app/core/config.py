"""
app/core/config.py
Central configuration for Infini (paths, models, constants).
"""

import os

# --- Base paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge", "md")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

# --- Model settings ---
EMBED_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "phi3"

# --- App metadata ---
APP_NAME = "Infini"
VERSION = "1.2"
AUTHOR = "Thomas Wolfe"

# --- Utility ---
def ensure_dirs():
    """Create required directories if missing."""
    for d in [KNOWLEDGE_DIR, CHROMA_DIR]:
        os.makedirs(d, exist_ok=True)

ensure_dirs()
