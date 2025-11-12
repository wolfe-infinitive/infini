import os
import json
import time
from hashlib import md5
from textwrap import dedent
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

# === Config ===
JSON_DIR = "knowledge/json"
MD_DIR = "knowledge/md"
CHROMA_DIR = "chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"

os.makedirs(MD_DIR, exist_ok=True)

# === 1️⃣ Utility: build markdown text from a JSON project ===
def json_to_markdown(data: dict) -> str:
    consultants_md = "\n".join(
        [f"- {c['name']} — {c['role']}" for c in data.get("consultants", [])]
    )
    contacts_md = "\n".join(
        [f"- {c['name']} — {c['title']}" for c in data.get("client_contacts", [])]
    )

    md = dedent(f"""
    # {data.get('title', 'Untitled Project')}

    **Client:** {data.get('client', 'N/A')}  
    **Industry:** {data.get('industry', 'N/A')}  
    **Duration:** {data.get('duration_months', '?')} months  
    **Team Size:** {data.get('team_size', '?')}  

    ## Summary
    {data.get('summary', '')}

    ## Tech Stack
    {', '.join(data.get('tech_stack', []))}

    ## Outcome
    {data.get('outcome', '')}

    ## Consultants
    {consultants_md}

    ## Client Contacts
    {contacts_md}
    """).strip()

    return md


# === 2️⃣ Utility: fingerprint a file’s contents ===
def file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return md5(f.read()).hexdigest()


# === 3️⃣ Track existing hashes to detect changes ===
HASH_FILE = ".sync_hashes.json"
hashes = {}
if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r", encoding="utf-8") as hf:
        hashes = json.load(hf)

updated_files = []
for fname in os.listdir(JSON_DIR):
    if not fname.endswith(".json"):
        continue
    fpath = os.path.join(JSON_DIR, fname)
    new_hash = file_hash(fpath)
    if hashes.get(fname) != new_hash:
        updated_files.append(fname)
        hashes[fname] = new_hash

if not updated_files:
    print("✅ No changes detected in JSON files.")
    exit(0)

# === 4️⃣ Regenerate Markdown for changed files ===
for file in updated_files:
    with open(os.path.join(JSON_DIR, file), "r", encoding="utf-8") as f:
        data = json.load(f)
    md_text = json_to_markdown(data)
    md_name = os.path.splitext(file)[0] + ".md"
    with open(os.path.join(MD_DIR, md_name), "w", encoding="utf-8") as mf:
        mf.write(md_text + "\n")
print(f"📝 Regenerated {len(updated_files)} Markdown files in '{MD_DIR}'")

# === 5️⃣ Update Chroma embeddings ===
embeddings = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)
db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

for file in updated_files:
    md_name = os.path.splitext(file)[0] + ".md"
    md_path = os.path.join(MD_DIR, md_name)
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Remove previous entries with same source metadata if any
    db._collection.delete(where={"source": md_name})
    # Add new document
    db.add_texts([text], metadatas=[{"source": md_name}])
    print(f"📚 Embedded: {md_name}")

db.persist()
print(f"✅ Synced {len(updated_files)} files → Chroma vector DB")

# === 6️⃣ Save updated hashes ===
with open(HASH_FILE, "w", encoding="utf-8") as hf:
    json.dump(hashes, hf, indent=2)