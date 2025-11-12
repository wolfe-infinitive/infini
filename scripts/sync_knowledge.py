"""
scripts/sync_knowledge.py
Rebuilds or updates the Chroma vector store from Markdown knowledge files.
"""

import os
import sys

# Ensure repo root is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import KNOWLEDGE_DIR, CHROMA_DIR
from app.core.rag_chain import RAGChain

def rebuild_vector_store():
    print("🔄 Syncing knowledge base and rebuilding vector store...")
    rag = RAGChain(knowledge_dir=KNOWLEDGE_DIR, chroma_dir=CHROMA_DIR)
    print("✅ Vector store successfully rebuilt at:", CHROMA_DIR)

if __name__ == "__main__":
    rebuild_vector_store()