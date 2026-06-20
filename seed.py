"""Seed a fresh DB with sample buyers + invoices so every endpoint has data."""
from datetime import date, timedelta
from app.database import SessionLocal, init_db
from app.models import Buyer, Invoice

init_db()
db = SessionLocal()
if db.query(Buyer).first():
    print("already seeded"); db.close(); raise SystemExit

data = [
    ("National Auto Components", "demo@example.com", "INV-2026-003", 95000, 65),
    ("Bharat Textiles",          "bt@example.com",   "INV-2026-002", 420000, 94),
    ("Sunrise Garments",         "sg@example.com",   "INV-2026-004", 240000, 33),
]
for name, email, num, amt, age in data:
    b = Buyer(name=name, email=email, language="en")
    db.add(b); db.commit(); db.refresh(b)
    db.add(Invoice(buyer_id=b.id, invoice_number=num, amount=amt,
                   invoice_date=date.today() - timedelta(days=age)))
db.commit(); db.close()
print(f"seeded {len(data)} buyers + invoices")
