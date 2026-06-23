from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Buyer, Invoice, EscalationEvent
from ..rules import calculate_interest, get_escalation_stage, is_eligible, RBI_BANK_RATE
from ..notify import send_notice
from ..drafting import draft_message
from ..config import settings
from ..schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceOut, InvoiceDetailOut,
    EscalationInput, EscalationEventOut, InterestCalcOut,
    SendRequest, SendResult,
)

router = APIRouter(prefix="/api", tags=["invoices"])


def _to_out(inv: Invoice, buyer: Buyer | None = None) -> InvoiceOut:
    calc = calculate_interest(float(inv.amount), inv.invoice_date, inv.due_date)
    return InvoiceOut(
        id=inv.id, buyer_id=inv.buyer_id, invoice_number=inv.invoice_number,
        amount=float(inv.amount), invoice_date=inv.invoice_date, due_date=inv.due_date,
        status=inv.status, escalation_stage=inv.escalation_stage,
        days_overdue=calc["msmedDaysOverdue"], interest_accrued=calc["totalInterest"],
        buyer_name=buyer.name if buyer else None,
        created_at=inv.created_at,
    )


def _event_out(e: EscalationEvent) -> EscalationEventOut:
    return EscalationEventOut(
        id=e.id, invoice_id=e.invoice_id, stage=e.stage, message=e.message,
        sent_at=e.sent_at, channel=e.channel, approved_by_owner=e.approved_by_owner,
        language=e.language,
    )


def _to_detail(inv: Invoice, buyer: Buyer | None, events: list[EscalationEvent]) -> InvoiceDetailOut:
    calc = calculate_interest(float(inv.amount), inv.invoice_date, inv.due_date)
    return InvoiceDetailOut(
        id=inv.id, buyer_id=inv.buyer_id, invoice_number=inv.invoice_number,
        amount=float(inv.amount), invoice_date=inv.invoice_date, due_date=inv.due_date,
        status=inv.status, escalation_stage=inv.escalation_stage,
        days_overdue=calc["msmedDaysOverdue"], interest_accrued=calc["totalInterest"],
        buyer_name=buyer.name if buyer else None,
        created_at=inv.created_at,
        escalation_events=[_event_out(e) for e in events],
    )


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(
    buyer_id: int | None = Query(default=None, alias="buyerId"),
    status: str | None = None,
    db: Session = Depends(get_db),
):
    q = select(Invoice, Buyer).join(Buyer)
    if buyer_id is not None:
        q = q.where(Invoice.buyer_id == buyer_id)
    if status is not None:
        q = q.where(Invoice.status == status)
    rows = db.execute(q).all()
    return [_to_out(inv, buyer) for inv, buyer in rows]


@router.get("/invoices/{id}", response_model=InvoiceDetailOut)
def get_invoice(id: int, db: Session = Depends(get_db)):
    row = db.execute(select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row
    events = db.execute(
        select(EscalationEvent)
        .where(EscalationEvent.invoice_id == id)
        .order_by(EscalationEvent.sent_at)
    ).scalars().all()
    return _to_detail(inv, buyer, list(events))


@router.patch("/invoices/{id}", response_model=InvoiceOut)
def update_invoice(id: int, body: InvoiceUpdate, db: Session = Depends(get_db)):
    row = db.execute(select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row
    if body.amount is not None:
        inv.amount = body.amount
    if body.due_date is not None:
        inv.due_date = body.due_date
    if body.status is not None:
        inv.status = body.status
    db.commit()
    db.refresh(inv)
    return _to_out(inv, buyer)


@router.post("/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(body: InvoiceCreate, db: Session = Depends(get_db)):
    inv = Invoice(
        buyer_id=body.buyer_id, invoice_number=body.invoice_number,
        amount=body.amount, invoice_date=body.invoice_date, due_date=body.due_date,
        escalation_stage=get_escalation_stage(body.invoice_date, body.due_date),
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
    db.execute(delete(EscalationEvent).where(EscalationEvent.invoice_id == id))
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


@router.post("/invoices/{id}/escalate", response_model=EscalationEventOut, status_code=status.HTTP_201_CREATED)
def escalate_invoice(id: int, body: EscalationInput, db: Session = Depends(get_db)):
    row = db.execute(select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row

    amount = float(inv.amount)
    calc = calculate_interest(amount, inv.invoice_date, inv.due_date)
    language = buyer.language or "English"

    if body.custom_message:
        message = body.custom_message
    else:
        message, _ = draft_message(
            stage=body.stage, buyer_name=buyer.name, invoice_number=inv.invoice_number,
            amount=amount, interest=calc["totalInterest"], total_due=calc["totalDue"],
            days_overdue=calc["msmedDaysOverdue"],
            rate_pct=round(calc["applicableRate"] * 100, 1),
            flag43bh=calc["section43bhApplies"], language=language,
        )

    event = EscalationEvent(
        invoice_id=inv.id, stage=body.stage, message=message,
        channel=body.channel, approved_by_owner=body.approved_by_owner, language=language,
    )
    db.add(event)
    inv.escalation_stage = body.stage
    inv.status = "escalating"
    db.commit()
    db.refresh(event)
    return _event_out(event)


@router.get("/invoices/{id}/interest", response_model=InterestCalcOut)
def get_invoice_interest(id: int, db: Session = Depends(get_db)):
    row = db.execute(select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row
    amount = float(inv.amount)
    calc = calculate_interest(amount, inv.invoice_date, inv.due_date)
    days = calc["msmedDaysOverdue"]
    daily = calc["totalInterest"] / days if days > 0 else 0.0
    eligible = is_eligible(inv.invoice_date, buyer.udyam_date)
    return InterestCalcOut(
        invoice_id=inv.id,
        principal_amount=amount,
        days_overdue=days,
        rbi_rate=float(RBI_BANK_RATE),
        applicable_rate=calc["applicableRate"],
        daily_interest=round(daily, 2),
        total_interest=calc["totalInterest"],
        total_due=calc["totalDue"],
        is_legally_overdue=days > 0,
        section_43bh_applies=calc["section43bhApplies"],
        eligible=eligible,
    )


@router.post("/invoices/{id}/send", response_model=SendResult)
def send_notice_route(id: int, body: SendRequest, db: Session = Depends(get_db)):
    row = db.execute(
        select(Invoice, Buyer).join(Buyer).where(Invoice.id == id)
    ).first()
    if row is None:
        raise HTTPException(404, "Invoice not found")
    inv, buyer = row

    amount = float(inv.amount)
    stage = body.stage or get_escalation_stage(inv.invoice_date, inv.due_date)
    language = body.language or buyer.language or "English"
    calc = calculate_interest(amount, inv.invoice_date, inv.due_date)

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

    # --- Resolve recipient (buyer email if valid, else demo fallback) --------
    def _valid(addr: str | None) -> str | None:
        return addr if addr and "@" in addr else None

    recipient = _valid(body.to) or _valid(buyer.email) or settings.demo_recipient_email
    if not recipient:
        raise HTTPException(422, "No recipient: add an email to the buyer or set demo_recipient_email")

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
    stage = get_escalation_stage(inv.invoice_date, inv.due_date)
    calc = calculate_interest(amount, inv.invoice_date, inv.due_date)
    message, source = draft_message(
        stage=stage, buyer_name=buyer.name, invoice_number=inv.invoice_number,
        amount=amount, interest=calc["totalInterest"], total_due=calc["totalDue"],
        days_overdue=calc["msmedDaysOverdue"],
        rate_pct=round(calc["applicableRate"] * 100, 1),
        flag43bh=calc["section43bhApplies"], language=buyer.language or "English",
    )
    return {"stage": stage, "source": source, "message": message}
