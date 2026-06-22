"""Seed a fresh DB with sample buyers + invoices so every endpoint has data."""
from datetime import date, timedelta
from app.database import SessionLocal, init_db
from app.models import Buyer, Invoice

init_db()
db = SessionLocal()
if db.query(Buyer).first():
    print("already seeded"); db.close(); raise SystemExit

# (name, email, udyam_date, invoice_number, amount, age_days)
# udyam_date BEFORE invoice_date  → eligible   (Silpi guardrail passes)
# udyam_date AFTER  invoice_date  → ineligible (Silpi guardrail blocks)
data = [
    # Eligible: registered 2 years before invoicing
    ("National Auto Components", "nac@example.com",
     date(2023, 4, 1),   "INV-2026-003", 95000,  65),

    # Eligible: registered well before invoice
    ("Bharat Textiles", "bt@example.com",
     date(2022, 9, 15),  "INV-2026-002", 420000, 94),

    # Ineligible: registered AFTER the invoice date (Silpi rule blocks this one)
    # invoice is ~33 days ago; udyam is only 10 days ago → postdates invoice
    ("Sunrise Garments", "sg@example.com",
     date.today() - timedelta(days=10), "INV-2026-004", 240000, 33),
]

for name, email, udyam_date, num, amt, age in data:
    b = Buyer(name=name, email=email, language="en", udyam_date=udyam_date)
    db.add(b); db.commit(); db.refresh(b)
    db.add(Invoice(
        buyer_id=b.id, invoice_number=num, amount=amt,
        invoice_date=date.today() - timedelta(days=age),
    ))

db.commit(); db.close()
print(f"seeded {len(data)} buyers + invoices")
print("  National Auto Components  udyam=2023-04-01  -> ELIGIBLE")
print("  Bharat Textiles           udyam=2022-09-15  -> ELIGIBLE")
print("  Sunrise Garments          udyam=2026-05-01  -> INELIGIBLE (postdates invoice)")
