import re
import time
import threading
from statistics import mean
from queue import Queue
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import ollama

from app.core.rag_chain import RAGChain
from app.core.config import KNOWLEDGE_DIR

# === Initialize FastAPI ===
app = FastAPI(title="Infini API", version="1.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Shared state ===
rag = RAGChain(knowledge_dir=KNOWLEDGE_DIR)
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


# === Non-streaming /ask ===
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    global cancel_flag
    if cancel_flag.is_set():
        cancel_flag.clear()

    history_text = "\n".join([f"User: {t['user']}\nInfini: {t['infini']}" for t in req.history])

    start = time.time()
    result = rag.query(req.query)
    elapsed = time.time() - start
    response_times.append(elapsed)

    answer = result.get("answer") or result.get("output") or str(result)
    answer = re.sub(r"^(Human:|Assistant:)\s*", "", answer.strip())
    sources = [doc.metadata.get("source") for doc in result.get("context", []) if doc.metadata.get("source")]

    return AskResponse(answer=answer, sources=list(set(sources)), elapsed_seconds=elapsed)


# === Streaming /ask/stream ===
@app.post("/ask/stream")
async def ask_stream(request: Request):
    body = await request.json()
    query = body.get("query")
    history = body.get("history", [])
    history_text = "\n".join([f"User: {t['user']}\nInfini: {t['infini']}" for t in history])

    def stream():
        start = time.time()
        prompt = f"You are Infini — Thomas Wolfe's assistant.\n\nHistory:\n{history_text}\n\nQuestion:\n{query}\n"
        for chunk in ollama.chat(model="phi3", messages=[{"role": "user", "content": prompt}], stream=True):
            if cancel_flag.is_set():
                break
            if "message" in chunk and "content" in chunk["message"]:
                yield f"data: {chunk['message']['content']}\n\n"
        elapsed = time.time() - start
        yield f"data: [END]|{elapsed:.2f}\n\n"

    return EventSourceResponse(stream())


# === Cancel & Stats ===
@app.post("/cancel")
def cancel():
    cancel_flag.set()
    return {"message": "Current request canceled."}


@app.get("/stats", response_model=StatsResponse)
def stats():
    avg_time = mean(response_times) if response_times else 0.0
    return StatsResponse(total_queries=len(response_times), avg_response_time=avg_time)


@app.get("/")
def root():
    return {"message": "Infini API is running 🚀"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)