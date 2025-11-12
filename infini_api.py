import os
import re
import time
import threading
import ollama
from queue import Queue
from statistics import mean
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from langchain_community.llms import Ollama
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

# === Configuration ===
KNOWLEDGE_DIR = "knowledge/md"
CHROMA_DIR = "chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "phi3"

app = FastAPI(title="Infini API", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cancel_flag = threading.Event()
response_times = []


# === Data Models ===
class AskRequest(BaseModel):
    query: str
    history: list[dict] = []


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    elapsed_seconds: float


class StatsResponse(BaseModel):
    total_queries: int
    avg_response_time: float


# === Knowledge loading ===
def load_documents():
    docs = []
    for file in os.listdir(KNOWLEDGE_DIR):
        path = os.path.join(KNOWLEDGE_DIR, file)
        if os.path.isfile(path) and file.endswith(".md"):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
                if text:
                    docs.append(Document(page_content=text, metadata={"source": file}))
    return docs


def get_vector_store(docs):
    embeddings = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    else:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_DIR)
        db.persist()
    return db


# === Build QA chain ===
def build_chain(streaming=False, callbacks=None):
    llm = Ollama(model=OLLAMA_MODEL)
    prompt = ChatPromptTemplate.from_template(
        "You are Infini — Thomas Wolfe's personal AI assistant and coding companion. "
        "Always respond in a concise, friendly, and professional tone. "
        "Never prefix messages with 'Human:' or 'Assistant:'. "
        "Use the provided context and conversation history to answer clearly.\n\n"
        "Conversation history:\n{history}\n\n"
        "Context:\n{context}\n\n"
        "Question:\n{input}"
    )
    combine_chain = create_stuff_documents_chain(llm, prompt)
    docs = load_documents()
    db = get_vector_store(docs)
    return create_retrieval_chain(db.as_retriever(), combine_chain)


# === Initialize persistent chain for non-streaming ===
qa_chain = build_chain()


# === /ask (non-streaming) ===
@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    global cancel_flag
    if cancel_flag.is_set():
        cancel_flag.clear()

    history_text = "\n".join([f"User: {t['user']}\nInfini: {t['infini']}" for t in request.history])

    start = time.time()
    result = qa_chain.invoke({"input": request.query, "history": history_text})
    elapsed = time.time() - start
    response_times.append(elapsed)

    answer = result.get("answer") or result.get("output") or str(result)
    answer = re.sub(r"^(Human:|Assistant:)\s*", "", answer.strip())
    sources = [doc.metadata.get("source") for doc in result.get("context", []) if doc.metadata.get("source")]

    return AskResponse(answer=answer, sources=list(set(sources)), elapsed_seconds=elapsed)


# === /ask/stream (streaming version) ===
@app.post("/ask/stream")
async def ask_stream(request: Request):
    body = await request.json()
    query = body.get("query")
    history = body.get("history", [])
    history_text = "\n".join([f"User: {t['user']}\nInfini: {t['infini']}" for t in history])

    def stream():
        start = time.time()
        prompt = f"You are Infini — Thomas Wolfe's assistant.\n\nHistory:\n{history_text}\n\nQuestion:\n{query}\n"
        for chunk in ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}], stream=True):
            if "message" in chunk and "content" in chunk["message"]:
                yield f"data: {chunk['message']['content']}\n\n"
        elapsed = time.time() - start
        yield f"data: [END]|{elapsed:.2f}\n\n"

    return EventSourceResponse(stream())


# === Cancel + Stats ===
@app.post("/cancel")
def cancel():
    cancel_flag.set()
    return {"message": "Current request canceled."}


@app.get("/stats", response_model=StatsResponse)
def get_stats():
    avg_time = mean(response_times) if response_times else 0.0
    return StatsResponse(total_queries=len(response_times), avg_response_time=avg_time)


@app.get("/")
def root():
    return {"message": "Infini API is running 🚀"}


# === Run ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)