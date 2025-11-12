# app/core/vector_store.py
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os

def build_vector_store(knowledge_dir, chroma_dir, embed_model="all-MiniLM-L6-v2"):
    embeddings = SentenceTransformerEmbeddings(model_name=embed_model)
    if os.path.exists(chroma_dir) and os.listdir(chroma_dir):
        return Chroma(persist_directory=chroma_dir, embedding_function=embeddings)
    docs = [Document(page_content=open(os.path.join(knowledge_dir, f), encoding="utf-8").read())
            for f in os.listdir(knowledge_dir) if f.endswith(".md")]
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    db = Chroma.from_documents(chunks, embeddings, persist_directory=chroma_dir)
    db.persist()
    return db