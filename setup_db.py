"""
setup_db.py — create the Bakaya schema in a fresh database.

This is the FastAPI equivalent of `drizzle-kit push`: it reads DATABASE_URL
(from .env or environment) and creates the three tables (buyers, invoices,
escalation_events) defined in app/models.py.

USE A SEPARATE DATABASE from your TypeScript app. Two ORMs managing one schema
will eventually fight. For a fresh Postgres:
    1. Create a new empty database (e.g. a new Neon project, or a new DB on Render).
    2. Put its connection string in .env as DATABASE_URL.
    3. Run:  python setup_db.py
    4. (optional) python seed.py    # adds sample rows

Run with --reset to DROP and recreate (wipes data — never point this at the TS db).
"""
import sys
from app.database import engine
from app.models import Base

if "--reset" in sys.argv:
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

print(f"Creating tables on: {engine.url}")
Base.metadata.create_all(bind=engine)
print("Done. Tables: buyers, invoices, escalation_events")
