import os, json, random
from faker import Faker

fake = Faker()

# === Directory setup ===
BASE_DIR = "knowledge/json"
os.makedirs(BASE_DIR, exist_ok=True)

# === Common vocab ===
industries = [
    "Finance", "Healthcare", "Retail", "Energy", "Education",
    "Telecommunications", "Manufacturing", "Insurance", "Public Sector"
]

tech_vocab = [
    ["Databricks", "Delta Lake", "Unity Catalog", "Python", "DQX"],
    ["AWS Glue", "S3", "Lambda", "Redshift", "MLflow"],
    ["Azure Synapse", "Fabric", "Power BI", "PySpark"],
    ["GCP BigQuery", "Vertex AI", "Looker Studio"],
    ["Snowflake", "dbt", "Airflow", "Tableau"],
    ["Kafka", "Spark Streaming", "FastAPI", "Docker", "Kubernetes"],
]

roles = [
    "Engagement Manager", "Project Manager", "Lead Data Engineer",
    "Cloud Architect", "Machine Learning Engineer",
    "Data Quality Analyst", "DevOps Engineer", "Business Analyst"
]

client_roles = [
    "CIO", "CTO", "Director of Data Engineering",
    "Head of Analytics", "VP of Technology", "Chief Architect"
]

focus_keywords = [
    "Data Platform Modernization", "AI-Powered Analytics",
    "Cloud Migration", "Data Quality Framework",
    "Real-Time Processing", "Predictive Modeling",
    "Governance and Compliance", "ETL Automation"
]


def random_consultants():
    team = []
    size = random.randint(4, 6)
    chosen_roles = random.sample(roles, size)
    for role in chosen_roles:
        team.append({
            "name": fake.first_name() + " " + fake.last_name(),
            "role": role
        })
    return team


def random_contacts():
    contacts = []
    for _ in range(random.randint(2, 3)):
        contacts.append({
            "name": fake.first_name() + " " + fake.last_name(),
            "title": random.choice(client_roles)
        })
    return contacts


def make_project(pid: int):
    client = fake.company().replace(",", "")
    focus = random.choice(focus_keywords)
    industry = random.choice(industries)
    title = f"{client.split()[0]} {focus}"
    summary = (
        f"{client} engaged our consulting team to deliver a {focus.lower()} solution. "
        f"We built scalable data pipelines, unified governance with Unity Catalog, "
        f"and deployed ML models using Databricks and MLflow for advanced analytics."
    )
    tech = random.choice(tech_vocab)
    outcome = random.choice([
        "Reduced data processing time by 40%.",
        "Improved model accuracy by 15% through better feature engineering.",
        "Lowered infrastructure cost by 25% using serverless ETL pipelines.",
        "Implemented end-to-end observability and automated DQX checks.",
        "Enabled real-time dashboards for executive visibility.",
    ])
    team_size = random.randint(4, 8)
    duration = random.randint(3, 12)

    return {
        "id": pid,
        "title": title,
        "client": client,
        "industry": industry,
        "summary": summary,
        "tech_stack": tech,
        "outcome": outcome,
        "team_size": team_size,
        "duration_months": duration,
        "consultants": random_consultants(),
        "client_contacts": random_contacts()
    }


# === Generate 50 projects ===
projects = [make_project(i + 1) for i in range(50)]

# === Write to individual files ===
for p in projects:
    safe_name = p["title"].replace(" ", "_").replace("/", "_")
    path = os.path.join(BASE_DIR, f"{safe_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2)

print(f"✅ Created {len(projects)} projects in '{BASE_DIR}'")
