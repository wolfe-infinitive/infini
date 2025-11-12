"""
tests/test_repo_health.py
Verifies that the Infini repository is healthy and all components load correctly.

Checks:
1. Core module imports and configs
2. Required directories exist
3. RAGChain initializes and builds Chroma vector store
4. Sample query returns a valid response
"""

import os
import sys
import time
import pytest

# === Path setup to ensure imports work no matter how pytest is run ===
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# === Imports from your core app ===
from app.core import config
from app.core.rag_chain import RAGChain


@pytest.mark.order(1)
def test_directories_exist():
    """Ensure required directories exist."""
    print(f"\n🔍 Checking directories at {config.BASE_DIR}")
    assert os.path.isdir(config.KNOWLEDGE_DIR), f"Missing directory: {config.KNOWLEDGE_DIR}"
    assert os.path.isdir(config.CHROMA_DIR), f"Missing directory: {config.CHROMA_DIR}"
    print("✅ Required directories exist.")


@pytest.mark.order(2)
def test_config_values():
    """Ensure config constants are valid."""
    print("\n⚙️  Validating configuration constants...")
    assert config.EMBED_MODEL.startswith("all-"), "Unexpected embedding model name."
    assert isinstance(config.OLLAMA_MODEL, str) and len(config.OLLAMA_MODEL) > 0
    assert os.path.exists(config.BASE_DIR), "Base directory path invalid."
    print(f"✅ Config valid — model={config.OLLAMA_MODEL}, embed={config.EMBED_MODEL}")


@pytest.mark.order(3)
def test_rag_chain_initialization():
    """Ensure RAGChain initializes and loads vector store."""
    print("\n🧠 Initializing RAGChain...")
    start = time.time()
    rag = RAGChain(
        knowledge_dir=config.KNOWLEDGE_DIR,
        chroma_dir=config.CHROMA_DIR,
        model=config.OLLAMA_MODEL
    )
    elapsed = time.time() - start
    assert rag is not None, "Failed to initialize RAGChain"
    assert rag.db is not None, "Vector store failed to load or build"
    print(f"✅ RAGChain initialized successfully in {elapsed:.2f}s")


@pytest.mark.order(4)
def test_sample_query():
    """Run a lightweight sample query to confirm model/chain health."""
    print("\n🤖 Running sample query through Infini...")
    rag = RAGChain()
    query = "What types of projects has Infini completed?"
    start = time.time()
    result = rag.query(query)
    elapsed = time.time() - start

    # Validate result
    assert isinstance(result, dict), "Query result should be a dictionary"
    answer = result.get("answer") or result.get("output") or str(result)
    assert len(answer.strip()) > 0, "Model returned empty response"

    print(f"✅ Query succeeded in {elapsed:.2f}s")
    print(f"🗣️  Model response preview:\n{answer[:250]}...\n")