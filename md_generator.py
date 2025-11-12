import os, json
from textwrap import dedent

JSON_DIR = "knowledge/json"
MD_DIR = "knowledge/md"
os.makedirs(MD_DIR, exist_ok=True)

def json_to_markdown(data: dict) -> str:
    """Render one project dict into markdown text for embedding."""
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


count = 0
for file in os.listdir(JSON_DIR):
    if not file.endswith(".json"):
        continue
    with open(os.path.join(JSON_DIR, file), "r", encoding="utf-8") as f:
        data = json.load(f)

    md_content = json_to_markdown(data)
    md_filename = os.path.splitext(file)[0] + ".md"
    with open(os.path.join(MD_DIR, md_filename), "w", encoding="utf-8") as mf:
        mf.write(md_content + "\n")
    count += 1

print(f"✅ Generated {count} Markdown files in '{MD_DIR}'")