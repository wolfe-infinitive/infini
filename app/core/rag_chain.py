"""
app/core/rag_chain.py
Reusable Retrieval-Augmented Generation (RAG) engine for Infini.
"""

import os
from langchain_community.llms import Ollama
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import KNOWLEDGE_DIR, CHROMA_DIR, EMBED_MODEL, OLLAMA_MODEL


class RAGChain:
    """
    Handles loading knowledge, building embeddings, and running queries.
    """

    def __init__(self, knowledge_dir: str = KNOWLEDGE_DIR, chroma_dir: str = CHROMA_DIR, model: str = OLLAMA_MODEL):
        self.knowledge_dir = knowledge_dir
        self.chroma_dir = chroma_dir
        self.model = model
        self.embeddings = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)
        self.db = self._load_or_create_chroma()
        self.llm = Ollama(model=self.model)
        self.chain = self._build_chain()

    # --- Internal helpers ---
    def _load_or_create_chroma(self):
        """Load existing Chroma DB or build a new one from Markdown files."""
        if os.path.exists(self.chroma_dir) and os.listdir(self.chroma_dir):
            print("📦 Loading existing Chroma DB...")
            return Chroma(persist_directory=self.chroma_dir, embedding_function=self.embeddings)

        print("🧠 Creating new Chroma DB from knowledge...")
        docs = []
        for file in os.listdir(self.knowledge_dir):
            path = os.path.join(self.knowledge_dir, file)
            if os.path.isfile(path) and file.endswith(".md"):
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                    if text:
                        docs.append(Document(page_content=text, metadata={"source": file}))

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        db = Chroma.from_documents(chunks, self.embeddings, persist_directory=self.chroma_dir)
        db.persist()
        print("✅ Chroma DB built and saved.")
        return db

    def _build_chain(self):
        """Create the retrieval + generation chain."""
        prompt = ChatPromptTemplate.from_template(
            "You are Infini — Thomas Wolfe's personal local assistant and coding companion.\n"
            "Use the provided context to answer concisely, clearly, and helpfully.\n\n"
            "Context:\n{context}\n\nQuestion:\n{input}"
        )
        combine_chain = create_stuff_documents_chain(self.llm, prompt)
        return create_retrieval_chain(self.db.as_retriever(), combine_chain)

    # --- Public interface ---
    def query(self, question: str):
        """Run a natural-language query through the chain."""
        return self.chain.invoke({"input": question})
