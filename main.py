import os
import sys
import time
import re
import threading
from queue import Queue
from collections import deque
from langchain_community.llms import Ollama
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


# === Configuration ===
KNOWLEDGE_DIR = "knowledge/md"
CHROMA_DIR = "chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "phi3"
MEMORY_TURNS = 5


# === Spinner with live timer ===
def spinner(stop_event, start_time):
    symbols = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        sys.stdout.write(
            f"\r💭 Infini is thinking... {symbols[idx % len(symbols)]}  ⏱️ {elapsed:5.1f}s"
        )
        sys.stdout.flush()
        time.sleep(0.1)
        idx += 1
    sys.stdout.write("\r" + " " * 70 + "\r")  # clear line


# === Load Markdown documents ===
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


# === Vector store ===
def get_vector_store(docs):
    embeddings = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        print("📦 Loading existing Chroma DB...")
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    else:
        print("🧠 Creating new Chroma DB from knowledge folder...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_DIR)
        db.persist()
        print("✅ Chroma DB built and saved.")
    return db


# === Build retrieval + generation chain ===
def build_chain(db):
    llm = Ollama(model=OLLAMA_MODEL)
    prompt = ChatPromptTemplate.from_template(
        "You are Infini — Thomas Wolfe's personal AI assistant and coding companion. "
        "Always respond in a friendly, concise, and professional tone. "
        "Never prefix messages with 'Human:' or 'Assistant:'. "
        "Use the provided context and recent conversation to answer clearly.\n\n"
        "Conversation history:\n{history}\n\n"
        "Context:\n{context}\n\n"
        "Question:\n{input}"
    )
    combine_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(db.as_retriever(), combine_chain)


# === Worker thread for LLM call ===
def llm_worker(qa_chain, query, history_text, output_queue, stop_event):
    try:
        result = qa_chain.invoke({"input": query, "history": history_text})
        output_queue.put(("result", result))
    except Exception as e:
        if not stop_event.is_set():
            output_queue.put(("error", e))


# === Interactive loop ===
def main():
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"❌ Missing folder '{KNOWLEDGE_DIR}'. Add Markdown files first.")
        return

    docs = load_documents()
    if not docs:
        print(f"⚠️ No Markdown files found in '{KNOWLEDGE_DIR}'. Run md_generator or sync_knowledge first.")
        return

    db = get_vector_store(docs)
    qa_chain = build_chain(db)
    memory = deque(maxlen=MEMORY_TURNS)

    print("\n🤖 Infini ready! Type your question (or 'exit' to quit)\n")

    while True:
        query = input("You: ").strip()
        if not query or query.lower() in {"exit", "quit"}:
            print("👋 Goodbye from Infini!")
            break

        history_text = "\n".join([f"User: {u}\nInfini: {a}" for u, a in memory])

        # Spinner + worker threads
        start_time = time.time()
        stop_event = threading.Event()
        output_queue = Queue()

        spinner_thread = threading.Thread(target=spinner, args=(stop_event, start_time))
        worker_thread = threading.Thread(
            target=llm_worker, args=(qa_chain, query, history_text, output_queue, stop_event)
        )

        spinner_thread.start()
        worker_thread.start()

        try:
            while worker_thread.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            # Cancel request
            stop_event.set()
            print("\n⚠️ Request canceled by user.\n")
            worker_thread.join(timeout=1)
            spinner_thread.join(timeout=1)
            continue

        stop_event.set()
        spinner_thread.join()
        worker_thread.join()

        elapsed = time.time() - start_time

        # Check output
        if not output_queue.empty():
            status, data = output_queue.get()
            if status == "error":
                print(f"\n⚠️ Error: {data}\n")
                continue
            result = data
        else:
            print("\n⚠️ No result returned.\n")
            continue

        # Clean and print
        answer = result.get("answer") or result.get("output") or str(result)
        answer = re.sub(r"^(Human:|Assistant:)\s*", "", answer.strip())

        print(f"\nInfini: {answer}")
        print(f"⏱️  Response time: {elapsed:.2f} seconds\n")

        if "context" in result and result["context"]:
            sources = [doc.metadata.get("source") for doc in result["context"] if doc.metadata.get("source")]
            if sources:
                print(f"📂 Sources: {', '.join(set(sources))}\n")

        memory.append((query, answer))


if __name__ == "__main__":
    main()