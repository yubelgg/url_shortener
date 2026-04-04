import csv
import json
import os

from dotenv import load_dotenv
from peewee import PostgresqlDatabase, chunked

load_dotenv()

# Connect directly (not through Flask app context)
db = PostgresqlDatabase(
    os.environ.get("DATABASE_NAME", "hackathon_db"),
    host=os.environ.get("DATABASE_HOST", "localhost"),
    port=int(os.environ.get("DATABASE_PORT", 5432)),
    user=os.environ.get("DATABASE_USER", "postgres"),
    password=os.environ.get("DATABASE_PASSWORD", "postgres"),
)

from app.models.user import User
from app.models.url import Url
from app.models.event import Event

# Point models at our direct connection
User._meta.database = db
Url._meta.database = db
Event._meta.database = db


def load_users(filepath="users.csv"):
    with open(filepath, newline="") as f:
        rows = list(csv.DictReader(f))

    with db.atomic():
        for batch in chunked(rows, 100):
            User.insert_many(batch).execute()

    print(f"Loaded {len(rows)} users")


def load_urls(filepath="urls.csv"):
    with open(filepath, newline="") as f:
        rows = list(csv.DictReader(f))

    # Convert is_active from Python string ("True"/"False") to boolean
    for row in rows:
        row["is_active"] = row["is_active"].strip() == "True"

    with db.atomic():
        for batch in chunked(rows, 100):
            Url.insert_many(batch).execute()

    print(f"Loaded {len(rows)} urls")


def load_events(filepath="events.csv"):
    with open(filepath, newline="") as f:
        rows = list(csv.DictReader(f))

    # Parse the details JSON string into a dict
    for row in rows:
        row["details"] = json.loads(row["details"])

    with db.atomic():
        for batch in chunked(rows, 100):
            Event.insert_many(batch).execute()

    print(f"Loaded {len(rows)} events")


def reset_sequences():
    """Reset auto-increment sequences after bulk insert with explicit IDs."""
    tables = [("users", "users_id_seq"), ("urls", "urls_id_seq"), ("events", "events_id_seq")]
    for table, seq in tables:
        db.execute_sql(f"SELECT setval('{seq}', (SELECT MAX(id) FROM {table}))")
    print("Reset auto-increment sequences")


if __name__ == "__main__":
    db.connect()
    db.create_tables([User, Url, Event])

    print("Seeding database...")
    load_users()
    load_urls()
    load_events()
    reset_sequences()

    db.close()
    print("Done!")
