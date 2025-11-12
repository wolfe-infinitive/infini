"""
scripts/generate_projects_json.py
Generates synthetic consulting project data in JSON format.
"""

import os
import sys
import json
import random
from faker import Faker

# Ensure repo root is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import KNOWLEDGE_DIR

# --- Configuration ---
OUTPUT_DIR = os.path.join(os.path.dirname(KNOWLEDGE_DIR), "json")
NUM_PROJECTS = 50
fake = Faker()

# --- Synthetic project generator ---
def generate_project(project_id: int):
    industries = ["Finance", "Retail", "Healthcare", "Manufacturing", "Technology", "Telecom", "Education"]
    tech_stack = [
        "Databricks", "Delta Lake", "Unity Catalog", "Python", "Spark", "MLflow",
        "AWS", "GCP", "Kafka", "Snowflake", "DQX", "Airflow"
    ]
    clients = [fake.company() for _ in range(50)]
    consultants = [fake.name() for _ in range(20)]
    contacts = [fake.name() for _ in range(20)]

    project = {
        "id": project_id,
        "title": f"{clients[project_id % len(clients)]} Data Platform Modernization",
        "client": clients[project_id % len(clients)],
        "industry": random.choice(industries),
        "summary": f"End-to-end modernization using {random.choice(tech_stack)} for analytics and AI workloads.",
        "tech_stack": random.sample(tech_stack, k=random.randint(4, 7)),
        "outcome": random.choice([
            "Reduced cost by 30%", "Cut ETL runtime by 45%", "Improved governance and lineage tracking",
            "Enabled real-time analytics", "Increased data accuracy by 20%"
        ]),
        "team_size": random.randint(4, 8),
        "duration_months": random.randint(3, 12),
        "consultants": random.sample(consultants, k=random.randint(3, 6)),
        "client_contacts": random.sample(contacts, k=random.randint(1, 3))
    }
    return project


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    projects = [generate_project(i + 1) for i in range(NUM_PROJECTS)]
    for project in projects:
        filename = project["title"].replace(" ", "_").replace("/", "-") + ".json"
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2)
    print(f"✅ Generated {NUM_PROJECTS} projects in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
