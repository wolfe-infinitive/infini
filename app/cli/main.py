import os
import re
import time
import threading
from app.core.rag_chain import RAGChain
from app.core.config import KNOWLEDGE_DIR

# === Initialize chain ===
rag = RAGChain(knowledge_dir=KNOWLEDGE_DIR)

cancel_flag = threading.Event()

def spinner_with_timer(stop_event):
    start_time = time.time()
    spinner = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        print(f"\r⏳ {spinner[idx % len(spinner)]}  Thinking... {elapsed:.1f}s", end="", flush=True)
        time.sleep(0.1)
        idx += 1
    total = time.time() - start_time
    print(f"\r✅ Done in {total:.2f}s\n")

def main():
    print("🤖 Infini is ready! Ask your question (type 'exit' to quit)\n")

    while True:
        query = input("You: ").strip()
        if not query or query.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break

        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=spinner_with_timer, args=(stop_event,))
        spinner_thread.start()

        try:
            result = rag.query(query)
            stop_event.set()
            spinner_thread.join()

            answer = result.get("answer") or result.get("output") or str(result)
            answer = re.sub(r"^(Human:|Assistant:)\s*", "", answer.strip())

            print(f"Infini: {answer}\n")

        except KeyboardInterrupt:
            stop_event.set()
            spinner_thread.join()
            print("\n🛑 Request canceled.\n")
        except Exception as e:
            stop_event.set()
            spinner_thread.join()
            print(f"\n⚠️ Error: {e}\n")

if __name__ == "__main__":
    main()