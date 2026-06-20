"""
Invoices router = your invoices.ts, in FastAPI form.

Study the three patterns here; every other route is a variation:

  1. Path params + DI:  Express `req.params.id` + imported `db`
                        → FastAPI `id: int` arg + `db: Session = Depends(get_db)`
  2. Validated body:    Express manual Zod parse of `req.body`
                        → FastAPI `body: InvoiceCreate` (auto-validated → 422)
  3. Response shaping:  Express `res.status(201).json({...})`
                        → `return Model(...)` with `response_model=` + status_code

The /send route is the showpiece: it reuses rules.py, notify.py, and (where you
plug it in) your Groq drafting — same orchestration as the TS version.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Buyer, Invoice, EscalationEvent
from ..rules import calculate_interest, get_escalation_stage
from ..notify import send_notice
from ..drafting import draft_message
from ..config import settings
from ..schemas import InvoiceCreate, InvoiceOut, SendRequest, SendResult

router = APIRouter(prefix="/api", tags=["invoices"])


def _to_out(inv: Invoice, buyer: Buyer | None = None) -> InvoiceOut:
    """Attach computed interest/stage, like the TS list/detail handlers do."""
    calc = calculate_interest(float(inv.amount), inv.invoice_date)
    return InvoiceOut(
        id=inv.id, buyer_id=inv.buyer_id, invoice_number=inv.invoice_number,
        amount=float(inv.amount), invoice_date=inv.invoice_date, due_date=inv.due_date,
        status=inv.status, escalation_stage=inv.escalation_stage,
        days_overdue=calc["msmedDaysOverdue"], interest_accrued=calc["totalInterest"],
        buyer_name=buyer.name if buyer else None,
    )


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(buyer_id: int | None = None, status: str | None = None, db: Session = Depends(get_db)):
    q = select(Invoice, Buyer).join(Buyer)
    if buyer_id is not None:
        q = q.where(Invoice.buyer_id == buyer_id)
    if status is not None:
        q = q.where(Invoice.status == status)
    rows = db.execute(q).all()
    return [_to_out(inv, buyer) for inv, buyer in rows]


@router.get("/invoices/{id}", response_model=InvoiceOut)
def get_invoice(id: int, db: Session = Depends(get_db)):
    row = db.execute(select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row
    return _to_out(inv, buyer)


@router.post("/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(body: InvoiceCreate, db: Session = Depends(get_db)):
    # body is already validated by Pydantic before we get here.
    inv = Invoice(
        buyer_id=body.buyer_id, invoice_number=body.invoice_number,
        amount=body.amount, invoice_date=body.invoice_date, due_date=body.due_date,
        escalation_stage=get_escalation_stage(body.invoice_date),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return _to_out(inv)


@router.delete("/invoices/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(id: int, db: Session = Depends(get_db)):
    inv = db.get(Invoice, id)
    if inv is None:
        raise HTTPException(404, "Invoice not found")
    db.delete(inv)
    db.commit()


@router.post("/invoices/{id}/mark-paid", response_model=InvoiceOut)
def mark_paid(id: int, db: Session = Depends(get_db)):
    row = db.execute(select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row
    inv.status = "paid"
    inv.escalation_stage = "none"
    db.commit()
    db.refresh(inv)
    return _to_out(inv, buyer)


@router.post("/invoices/{id}/send", response_model=SendResult)
def send_notice_route(id: int, body: SendRequest, db: Session = Depends(get_db)):
    row = db.execute(
        select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)
    ).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row

    amount = float(inv.amount)
    stage = body.stage or get_escalation_stage(inv.invoice_date)
    language = body.language or buyer.language or "English"
    calc = calculate_interest(amount, inv.invoice_date)

    # --- Draft the message --------------------------------------------------
    # In the real app this calls Groq (your drafting.py). For the skeleton we
    # use a deterministic template so it runs with no API key. Swap in Groq here.
    message, source = draft_message(
        stage=stage, buyer_name=buyer.name, invoice_number=inv.invoice_number,
        amount=amount, interest=calc["totalInterest"], total_due=calc["totalDue"],
        days_overdue=calc["msmedDaysOverdue"],
        rate_pct=round(calc["applicableRate"] * 100, 1),
        flag43bh=calc["section43bhApplies"], language=language,
    )

    # --- Resolve recipient (demo override → buyer email) --------------------
    recipient = body.to or settings.demo_recipient_email or buyer.email
    if not recipient:
        raise HTTPException(422, "No recipient: set demo_recipient_email or buyer email")

    # --- Send + log + advance stage -----------------------------------------
    delivery = send_notice(to=recipient, subject=f"Payment Notice — Invoice {inv.invoice_number}", body=message)

    db.add(EscalationEvent(
        invoice_id=inv.id, stage=stage, message=message,
        channel="email", approved_by_owner=True, language=language,
    ))
    inv.escalation_stage = stage
    inv.status = "escalating"
    db.commit()

    return SendResult(
        stage=stage, source=source, message=message,
        delivery_status=delivery["status"], delivery_detail=delivery["detail"],
        recipient=recipient,
    )


@router.post("/invoices/{id}/draft")
def draft_only(id: int, db: Session = Depends(get_db)):
    """Draft a notice WITHOUT sending — twin of /api/draft in the TS app."""
    row = db.execute(select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row
    amount = float(inv.amount)
    stage = get_escalation_stage(inv.invoice_date)
    calc = calculate_interest(amount, inv.invoice_date)
    message, source = draft_message(
        stage=stage, buyer_name=buyer.name, invoice_number=inv.invoice_number,
        amount=amount, interest=calc["totalInterest"], total_due=calc["totalDue"],
        days_overdue=calc["msmedDaysOverdue"],
        rate_pct=round(calc["applicableRate"] * 100, 1),
        flag43bh=calc["section43bhApplies"], language=buyer.language or "English",
    )
    return {"stage": stage, "source": source, "message": message}
