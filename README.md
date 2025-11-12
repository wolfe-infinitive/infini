# 🧠 Infini — Local AI Assistant

Infini is a **local, privacy-first small language model (SLM)** designed to serve as a personalized coding companion and knowledge assistant.  
It runs entirely on your machine using [Ollama](https://ollama.com), [LangChain](https://www.langchain.com/), and [FastAPI](https://fastapi.tiangolo.com/), powered by your own knowledge base stored in Markdown or JSON.

---

## 🚀 Features

- **Local & Private** — all inference runs through your local Ollama server.
- **Retrieval-Augmented Generation (RAG)** — connects your knowledge (`/knowledge/md`) with a Chroma vector store.
- **Streaming Responses** — tokens flow live from the model for real-time interactivity.
- **API-Ready** — serves a REST + SSE API for integration with a front-end UI.
- **Extendable** — easily plug in more models, add new knowledge, or integrate a web front-end.

---

## 🧩 Architecture

```
┌────────────────────────┐
│   React / Frontend UI  │  ← (optional, connects via SSE)
└──────────┬─────────────┘
           │
     [ FastAPI Server ]
           │
           ▼
     LangChain Retriever
           │
           ▼
   Ollama Local Model (phi3)
           │
           ▼
   knowledge/md + chroma_db
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/infini-local.git
cd infini-local
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # (Mac/Linux)
# or
.\.venv\Scripts\activate   # (Windows)
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Ollama

Make sure [Ollama](https://ollama.com) is installed and running locally:

```bash
ollama serve
```

Pull your base model (for example Phi-3):

```bash
ollama pull phi3
```

### 5. Run the API

```bash
python infini_api.py
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 💬 API Endpoints

| Endpoint      | Method | Description                                          |
| ------------- | ------ | ---------------------------------------------------- |
| `/ask`        | POST   | Returns a full JSON response (non-streaming).        |
| `/ask/stream` | POST   | Streams tokens live via Server-Sent Events (SSE).    |
| `/cancel`     | POST   | Cancels an active request.                           |
| `/stats`      | GET    | Returns total query count and average response time. |
| `/`           | GET    | Health check (“Infini API is running 🚀”).           |

### Example Request

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Which projects used MLflow?"}'
```

### Example Streaming

```bash
curl -N -X POST http://127.0.0.1:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the Retail360 project."}'
```

---

## 📚 Knowledge Base

Place all your knowledge files in:

```
knowledge/md/
```

You can generate them from JSON, Markdown notes, or project data.  
When the API starts, it automatically builds or updates the `chroma_db` index for retrieval.

---

## 🧠 Example Use Cases

- Personal coding assistant trained on your projects
- Company-specific data knowledge base (private RAG)
- Databricks / MLflow / DQX pipeline query tool
- Local alternative to cloud LLMs

---

## 🧰 Optional Frontend (Coming Soon)

A React chat interface can connect directly to `/ask/stream`  
for real-time conversation, cancel button, and response timer.

To preview it later:

```bash
cd frontend
npm install
npm run dev
```

---

## 🧾 License

This project is for **personal and educational use**.  
Feel free to modify, extend, and self-host your own Infini instance.

---

### ✨ Credits

- **Thomas Wolfe** — concept, architecture, and implementation
- **Ollama** — local model hosting
- **LangChain** + **Chroma** — RAG engine
- **FastAPI** — backend API server
