import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"

COMPANIES = [
    "Mistral AI", "Databricks", "UiPath", "Hugging Face", "Anthropic", "OpenAI",
    "DeepMind", "Cohere", "Scale AI", "Weights & Biases", "Palantir", "Snowflake",
    "NVIDIA", "Meta AI", "Google Research", "Microsoft Research", "Apple ML",
    "Amazon Science", "Tesla AI", "Stability AI", "Perplexity AI", "ElevenLabs",
    "Criteo", "Dataiku", "Doctolib", "Alan", "Qonto", "Revolut", "Stripe",
    "Spotify", "Booking.com", "Adyen", "ASML", "Bosch AI", "Siemens Digital",
    "SAP Labs", "Bitdefender", "Adobe Research", "Cloudflare", "Datadog",
]

ROLES = [
    "AI Engineer Intern", "Machine Learning Engineer", "NLP Research Intern",
    "Applied Scientist Intern", "LLM Evaluation Engineer", "AI Security Analyst",
    "Data Scientist", "MLOps & Infrastructure Engineer", "Computer Vision Intern",
    "Deep Learning Research Engineer", "Generative AI Developer", "Backend & AI Systems Engineer",
]

NOTES_POOL = [
    "Applied via careers portal",
    "Referred by university alumni",
    "Completed online coding assessment",
    "Technical phone screen scheduled",
    "Submitted GitHub portfolio & Master's thesis",
    "Recruiter reached out on LinkedIn",
    "Awaiting feedback after system design round",
    "Automated application confirmation received",
]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(target_rows: int = 2500) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Applied',
                applied_date TEXT NOT NULL,
                last_contact_date TEXT NOT NULL,
                notes TEXT DEFAULT ''
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        if count < 100:
            conn.execute("DELETE FROM applications")
            rng = random.Random(42)
            today = datetime.now().date()
            statuses = ["Applied", "Interviewing", "Rejected", "Offer"]
            weights = [0.46, 0.24, 0.25, 0.05]

            rows_to_insert = []
            for i in range(target_rows):
                comp = f"{rng.choice(COMPANIES)} (#{i + 1})" if i >= len(COMPANIES) else rng.choice(COMPANIES)
                # Keep clean company names for easy aggregation
                comp_clean = rng.choice(COMPANIES)
                role = rng.choice(ROLES)
                status = rng.choices(statuses, weights=weights, k=1)[0]
                days_ago_applied = rng.randint(1, 90)
                days_since_contact = rng.randint(0, min(days_ago_applied, 35))
                applied_date = str(today - timedelta(days=days_ago_applied))
                last_contact_date = str(today - timedelta(days=days_since_contact))
                note = rng.choice(NOTES_POOL)
                rows_to_insert.append((comp_clean, role, status, applied_date, last_contact_date, note))

            conn.executemany(
                """
                INSERT INTO applications (company, role, status, applied_date, last_contact_date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows_to_insert,
            )
