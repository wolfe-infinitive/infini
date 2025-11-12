"""
scripts/md_generator.py
Converts generated JSON projects into Markdown knowledge files.
"""

import os
import sys
import json

# Ensure repo root is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import KNOWLEDGE_DIR

JSON_DIR = os.path.join(os.path.dirname(KNOWLEDGE_DIR), "json")
MD_DIR = KNOWLEDGE_DIR

def json_to_markdown(data: dict) -> str:
    """Convert a single project JSON dict to Markdown format."""
    lines = [
        f"# {data['title']}",
        "",
        f"**Client:** {data['client']}",
        f"**Industry:** {data['industry']}",
        f"**Duration:** {data['duration_months']} months",
        f"**Team Size:** {data['team_size']}",
        "",
        "## Summary",
        data["summary"],
        "",
        "## Tech Stack",
        ", ".join(data["tech_stack"]),
        "",
        "## Outcome",
        data["outcome"],
        "",
        "## Consultants",
        ", ".join(data["consultants"]),
        "",
        "## Client Contacts",
        ", ".join(data["client_contacts"]),
    ]
    return "\n".join(lines)

def main():
    os.makedirs(MD_DIR, exist_ok=True)
    count = 0
    for file in os.listdir(JSON_DIR):
        if not file.endswith(".json"):
            continue
        path = os.path.join(JSON_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        md_text = json_to_markdown(data)
        md_filename = file.replace(".json", ".md")
        md_path = os.path.join(MD_DIR, md_filename)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        count += 1
    print(f"✅ Converted {count} JSON projects to Markdown in {MD_DIR}")

if __name__ == "__main__":
    main()
